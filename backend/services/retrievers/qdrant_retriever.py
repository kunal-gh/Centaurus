"""
Centaurus Qdrant Retriever Service.
Manages Qdrant vector database ingestion, indexing, and hybrid (dense + sparse) retrieval.

Retrieval pipeline:
  1. Dense (BAAI/bge-small-en-v1.5) + Sparse (BM25) prefetch
  2. Reciprocal Rank Fusion (RRF) to merge ranked lists
  3. Cross-encoder reranking (ms-marco-MiniLM-L-6-v2) for precision boosting
"""
import os
import traceback
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import PointStruct, VectorParams, Distance, SparseVectorParams

from backend.config import settings
from backend.services.retrievers.chunker import chunk_markdown_file
from backend.services.retrievers.embeddings import get_embedding, get_embedding_dim

_QDRANT_CLIENT = None
_SPARSE_MODEL = None
_RERANKER = None

COLLECTION_NAME = "centaurus_kb"


# ─── Client & Model Lazy Loaders ─────────────────────────────────────────────

def get_qdrant_client() -> QdrantClient:
    """
    Initializes and returns the Qdrant client.
    Defaults to a local file-based SQLite-backed database for offline execution.
    Override with QDRANT_URL + QDRANT_API_KEY env vars for cloud (Qdrant Cloud free tier).
    """
    global _QDRANT_CLIENT
    if _QDRANT_CLIENT is None:
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_key = os.getenv("QDRANT_API_KEY")
        if qdrant_url:
            _QDRANT_CLIENT = QdrantClient(url=qdrant_url, api_key=qdrant_key)
        else:
            os.makedirs("knowledge_base", exist_ok=True)
            _QDRANT_CLIENT = QdrantClient(path="knowledge_base/qdrant_db")
    return _QDRANT_CLIENT


def get_sparse_model():
    """
    Lazy-loads the FastEmbed BM25 sparse embedding model.
    Used as the keyword (lexical) component in hybrid retrieval.
    """
    global _SPARSE_MODEL
    if _SPARSE_MODEL is None:
        if settings.is_mock_mode:
            return None
        try:
            from fastembed import SparseTextEmbedding
            _SPARSE_MODEL = SparseTextEmbedding(model_name="Qdrant/bm25")
        except Exception as e:
            print(f"[Qdrant] Warning: SparseTextEmbedding unavailable: {e}")
            _SPARSE_MODEL = None
    return _SPARSE_MODEL


def get_reranker():
    """
    Lazy-loads the local cross-encoder reranker model.
    Uses 'cross-encoder/ms-marco-MiniLM-L-6-v2' (22M params, CPU-friendly).
    Scores (query, passage) pairs directly for high-precision re-ordering
    after the RRF fusion stage.
    Falls back gracefully to None (passthrough, no reranking) if unavailable.
    """
    global _RERANKER
    if _RERANKER is None:
        if settings.is_mock_mode:
            return None
        try:
            from sentence_transformers import CrossEncoder
            _RERANKER = CrossEncoder(
                "cross-encoder/ms-marco-MiniLM-L-6-v2",
                max_length=512,
            )
            print("[Qdrant] Cross-encoder reranker loaded: ms-marco-MiniLM-L-6-v2")
        except Exception as e:
            print(f"[Qdrant] Warning: CrossEncoder unavailable: {e}. Skipping reranking.")
            _RERANKER = None
    return _RERANKER


# ─── Collection Management ─────────────────────────────────────────────────────

def init_collection(force_recreate: bool = False):
    """
    Sets up the Qdrant collection for hybrid (dense + sparse) retrieval.
    Ingests all knowledge base markdown documents on initialization.

    Uses delete+create instead of the deprecated recreate_collection().
    """
    if settings.is_mock_mode:
        print("[Qdrant] Mock mode active — skipping collection initialization.")
        return

    client = get_qdrant_client()

    # Check existence
    try:
        collections = client.get_collections().collections
        exists = any(c.name == COLLECTION_NAME for c in collections)
    except Exception:
        exists = False

    if exists and not force_recreate:
        print(f"[Qdrant] Collection '{COLLECTION_NAME}' already exists — skipping init.")
        return

    # Tear down if force recreate
    if exists:
        print(f"[Qdrant] Dropping existing collection '{COLLECTION_NAME}'...")
        client.delete_collection(COLLECTION_NAME)

    print(f"[Qdrant] Creating collection '{COLLECTION_NAME}'...")
    dim = get_embedding_dim()

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        sparse_vectors_config={
            "text-sparse": SparseVectorParams(
                index=models.SparseIndexParams(on_disk=False)
            )
        },
    )

    # Ingest the operations manual
    ops_manual_path = "knowledge_base/centaurus_ops_manual.md"
    if not os.path.exists(ops_manual_path):
        print(f"[Qdrant] Warning: {ops_manual_path} not found — collection created empty.")
        return

    chunks = chunk_markdown_file(ops_manual_path)
    points = []
    sparse_model = get_sparse_model()

    for idx, chunk in enumerate(chunks):
        dense_vector = get_embedding(chunk.text)

        sparse_vector_data = None
        if sparse_model:
            try:
                sparse_emb = list(sparse_model.embed([chunk.text]))[0]
                sparse_vector_data = models.SparseVector(
                    indices=sparse_emb.indices.tolist(),
                    values=sparse_emb.values.tolist(),
                )
            except Exception as e:
                print(f"[Qdrant] Sparse embedding failed for chunk {idx}: {e}")

        vectors: dict = {"": dense_vector}
        if sparse_vector_data:
            vectors["text-sparse"] = sparse_vector_data

        points.append(PointStruct(
            id=idx,
            vector=vectors,
            payload={
                "text": chunk.text,
                "chunk_id": chunk.chunk_id,
                **chunk.metadata,
            },
        ))

    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"[Qdrant] Ingested {len(points)} chunks into '{COLLECTION_NAME}'.")


# ─── Search ────────────────────────────────────────────────────────────────────

def search_hybrid(
    query: str,
    top_k: int = 3,
    prefetch_k: int = 10,
    rerank: bool = True,
) -> List[Dict[str, Any]]:
    """
    Three-stage hybrid retrieval pipeline:

    Stage 1 — Prefetch
      Dense vector (BAAI/bge-small-en-v1.5 cosine) + BM25 sparse keyword search.
      Each retrieves up to prefetch_k candidates independently.

    Stage 2 — RRF Fusion
      Qdrant's built-in Reciprocal Rank Fusion merges both ranked lists into a
      single unified ranking without requiring score normalization.

    Stage 3 — Cross-Encoder Reranking
      (query, passage) pairs are scored by ms-marco-MiniLM-L-6-v2.
      This produces the highest-precision final ranking at minimal CPU cost.

    Returns top_k results with full metadata payload.
    """
    if settings.is_mock_mode:
        return []

    client = get_qdrant_client()
    dense_vector = get_embedding(query)
    sparse_model = get_sparse_model()

    # Stage 1: Build prefetch queries
    prefetch_queries = [
        models.Prefetch(query=dense_vector, limit=prefetch_k),
    ]

    if sparse_model:
        try:
            sparse_emb = list(sparse_model.embed([query]))[0]
            sparse_vector = models.SparseVector(
                indices=sparse_emb.indices.tolist(),
                values=sparse_emb.values.tolist(),
            )
            prefetch_queries.append(
                models.Prefetch(
                    query=sparse_vector,
                    using="text-sparse",
                    limit=prefetch_k,
                )
            )
        except Exception as e:
            print(f"[Qdrant] Query sparse embedding failed: {e}")

    # Stage 2: RRF fusion — pull wider set for reranker to work with
    try:
        rrf_k = min(prefetch_k, max(top_k * 3, 6))
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            prefetch=prefetch_queries,
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=rrf_k,
        )
    except Exception as exc:
        print(f"[Qdrant] query_points failed: {exc}")
        traceback.print_exc()
        return []

    candidates = []
    for point in results.points:
        candidates.append({
            "text": point.payload.get("text", ""),
            "score": point.score,
            "metadata": {
                "chunk_id": point.payload.get("chunk_id"),
                "section": point.payload.get("section"),
                "source": point.payload.get("source"),
                "category": point.payload.get("category"),
                "document_title": point.payload.get("document_title"),
            },
        })

    if not candidates:
        return []

    # Stage 3: Cross-encoder reranking
    if rerank and len(candidates) > 1:
        reranker = get_reranker()
        if reranker:
            try:
                pairs = [(query, c["text"]) for c in candidates]
                ce_scores = reranker.predict(pairs).tolist()
                for doc, score in zip(candidates, ce_scores):
                    doc["score"] = float(score)
                candidates.sort(key=lambda x: x["score"], reverse=True)
            except Exception as e:
                print(f"[Qdrant] Cross-encoder reranking failed: {e}. Using RRF order.")

    return candidates[:top_k]
