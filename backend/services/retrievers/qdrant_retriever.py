"""
Centaurus Qdrant Retriever Service.
Manages Qdrant vector database ingestion, indexing, and hybrid (dense + sparse) retrieval.
"""
import os
import traceback
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import PointStruct, VectorParams, Distance, SparseVectorParams, NamedSparseVector

from backend.config import settings
from backend.services.retrievers.chunker import chunk_markdown_file
from backend.services.retrievers.embeddings import get_embedding, get_embedding_dim

_QDRANT_CLIENT = None
_SPARSE_MODEL = None

def get_qdrant_client() -> QdrantClient:
    """
    Initializes and returns the Qdrant client.
    Defaults to a local, file-based database for offline execution without Docker.
    """
    global _QDRANT_CLIENT
    if _QDRANT_CLIENT is None:
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_key = os.getenv("QDRANT_API_KEY")
        if qdrant_url:
            _QDRANT_CLIENT = QdrantClient(url=qdrant_url, api_key=qdrant_key)
        else:
            os.makedirs("knowledge_base", exist_ok=True)
            # Use local SQLite-backed Qdrant store
            _QDRANT_CLIENT = QdrantClient(path="knowledge_base/qdrant_db")
    return _QDRANT_CLIENT

def get_sparse_model():
    """
    Lazy loads the FastEmbed SparseTextEmbedding model (BM25) for keyword extraction.
    """
    global _SPARSE_MODEL
    if _SPARSE_MODEL is None:
        if settings.is_mock_mode:
            return None
        try:
            from fastembed import SparseTextEmbedding
            # Standard BM25 model for sparse vector generation
            _SPARSE_MODEL = SparseTextEmbedding(model_name="Qdrant/bm25")
        except Exception as e:
            print(f"Warning: could not import SparseTextEmbedding: {e}.")
            _SPARSE_MODEL = None
    return _SPARSE_MODEL

def init_collection(collection_name: str = "centaurus_kb", force_recreate: bool = False):
    """
    Sets up the Qdrant collection for hybrid (dense + sparse) retrieval.
    Ingests all manual markdown documents on initialization.
    """
    if settings.is_mock_mode:
        print("Mock mode active. Skipping Qdrant collection initialization.")
        return

    client = get_qdrant_client()
    exists = False
    try:
        collections = client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
    except Exception:
        # Ignore errors during initial lookup
        pass

    if exists and not force_recreate:
        print(f"Qdrant collection '{collection_name}' already exists.")
        return

    print(f"Initializing Qdrant collection: {collection_name}...")
    dim = get_embedding_dim()

    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=dim,
            distance=Distance.COSINE
        ),
        sparse_vectors_config={
            "text-sparse": SparseVectorParams(
                index=models.SparseIndexParams(
                    on_disk=False,
                )
            )
        }
    )

    # Ingest the operations manual
    ops_manual_path = "knowledge_base/centaurus_ops_manual.md"
    if os.path.exists(ops_manual_path):
        chunks = chunk_markdown_file(ops_manual_path)
        points = []
        sparse_model = get_sparse_model()

        for idx, chunk in enumerate(chunks):
            # Dense Embedding
            dense_vector = get_embedding(chunk.text)
            
            # Sparse Embedding (BM25)
            sparse_vector_data = None
            if sparse_model:
                try:
                    embeddings_generator = sparse_model.embed([chunk.text])
                    sparse_emb = list(embeddings_generator)[0]
                    sparse_vector_data = models.SparseVector(
                        indices=sparse_emb.indices.tolist(),
                        values=sparse_emb.values.tolist()
                    )
                except Exception as e:
                    print(f"Sparse embedding failed for chunk {idx}: {e}")

            vectors = {
                "": dense_vector, # Primary default vector is dense
            }
            if sparse_vector_data:
                vectors["text-sparse"] = sparse_vector_data

            points.append(PointStruct(
                id=idx,
                vector=vectors,
                payload={
                    "text": chunk.text,
                    "chunk_id": chunk.chunk_id,
                    **chunk.metadata
                }
            ))

        if points:
            client.upsert(
                collection_name=collection_name,
                points=points
            )
            print(f"Ingested {len(points)} chunks into '{collection_name}'.")

def search_hybrid(query: str, collection_name: str = "centaurus_kb", top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Performs a hybrid search (Dense + Sparse) with Reciprocal Rank Fusion (RRF) in Qdrant.
    """
    if settings.is_mock_mode:
        return []

    client = get_qdrant_client()
    dense_vector = get_embedding(query)
    sparse_model = get_sparse_model()

    # Define dense query prefetch
    prefetch_queries = [
        models.Prefetch(
            query=dense_vector,
            limit=10,
        )
    ]

    # Add sparse query prefetch if model is available
    if sparse_model:
        try:
            embeddings_generator = sparse_model.embed([query])
            sparse_emb = list(embeddings_generator)[0]
            sparse_vector = models.SparseVector(
                indices=sparse_emb.indices.tolist(),
                values=sparse_emb.values.tolist()
            )
            prefetch_queries.append(
                models.Prefetch(
                    query=sparse_vector,
                    using="text-sparse",
                    limit=10,
                )
            )
        except Exception as e:
            print(f"Failed to generate query sparse vector: {e}")

    try:
        # Execute Query Points with Reciprocal Rank Fusion
        results = client.query_points(
            collection_name=collection_name,
            prefetch=prefetch_queries,
            query=models.FusionQuery(
                fusion=models.Fusion.RRF
            ),
            limit=top_k
        )

        matched_docs = []
        for point in results.points:
            matched_docs.append({
                "text": point.payload.get("text"),
                "score": point.score,
                "metadata": {
                    "chunk_id": point.payload.get("chunk_id"),
                    "section": point.payload.get("section"),
                    "source": point.payload.get("source"),
                    "category": point.payload.get("category"),
                    "document_title": point.payload.get("document_title")
                }
            })
        return matched_docs
    except Exception as exc:
        print(f"Qdrant query failed: {exc}")
        traceback.print_exc()
        return []
