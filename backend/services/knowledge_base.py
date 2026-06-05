"""
RAG pipeline using OpenAI embeddings and NumPy cosine similarity.
In-memory only. No external vector database required for MVP.
Spec Reference: Section 6.6
"""
import os
import json
import numpy as np
from openai import OpenAI
from backend.config import settings

client = None if settings.is_mock_mode else OpenAI(api_key=settings.OPENAI_API_KEY)

# Global in-memory cache — populated once at startup, reused for all queries
_KB_ENTRIES = None


def _get_embedding(text: str) -> list:
    """
    Generates embedding vector using OpenAI text-embedding-3-small.
    Input is truncated to 8000 chars as a safety measure.
    """
    if settings.is_mock_mode:
        raise RuntimeError("Embeddings are disabled in mock mode")

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000]  # Safety truncation
    )
    return response.data[0].embedding


def _cosine_similarity(a: list, b: list) -> float:
    """
    Computes cosine similarity between two embedding vectors using NumPy.
    Returns 0.0 if either vector has zero norm.
    """
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    dot = np.dot(a_arr, b_arr)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def _chunk_markdown(file_path: str = "knowledge_base/centaurus_ops_manual.md") -> list:
    """
    Splits markdown KB file into chunks by ## headers.
    Each ## section becomes one independently retrievable chunk.
    Only includes sections longer than 50 characters to exclude empty headers.
    """
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    chunks = []
    for section in content.split("## "):
        section = section.strip()
        if len(section) > 50:
            chunks.append("## " + section)

    return chunks


def build_kb_cache(
    file_path: str = "knowledge_base/centaurus_ops_manual.md",
    cache_path: str = "knowledge_base/kb_embeddings.json"
) -> list:
    """
    Loads KB from markdown, embeds each chunk, and caches to disk.
    Call once at application startup via @app.on_event("startup").

    Priority order:
    1. In-memory global cache (_KB_ENTRIES)
    2. Disk cache (kb_embeddings.json)
    3. Fresh embedding from OpenAI API
    """
    global _KB_ENTRIES

    if _KB_ENTRIES is not None:
        return _KB_ENTRIES

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            _KB_ENTRIES = json.load(f)
        return _KB_ENTRIES

    # In mock mode, we avoid external embedding calls and keep KB as raw chunks.
    if settings.is_mock_mode:
        _KB_ENTRIES = [{"text": c, "embedding": None} for c in _chunk_markdown(file_path)]
        return _KB_ENTRIES

    chunks = _chunk_markdown(file_path)
    if not chunks:
        _KB_ENTRIES = []
        return _KB_ENTRIES

    entries = []
    for chunk in chunks:
        embedding = _get_embedding(chunk)
        entries.append({"text": chunk, "embedding": embedding})

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(entries, f)

    _KB_ENTRIES = entries
    return _KB_ENTRIES


def search_knowledge_base(query: str, top_k: int = 1) -> tuple:
    """
    Semantic search over KB chunks using cosine similarity.

    Args:
        query: User query string
        top_k: Number of top matches to consider (default 1 for MVP)

    Returns:
        Tuple: (best_matching_text or None, relevance_score 0.0-1.0)
        Returns (None, score) if best score < 0.5 threshold.
    """
    kb = build_kb_cache()
    if not kb:
        return None, 0.0

    # Mock mode: keyword overlap scoring on chunk text.
    if settings.is_mock_mode:
        q = (query or "").lower()
        q_terms = {t for t in q.replace("?", " ").replace(".", " ").split() if len(t) > 2}
        best_text, best_score = None, 0.0
        for entry in kb:
            c = entry["text"]
            c_terms = {t for t in c.lower().replace("?", " ").replace(".", " ").split() if len(t) > 2}
            overlap = len(q_terms & c_terms) if q_terms else 0
            score = overlap / max(len(q_terms), 1)
            if score > best_score:
                best_score = score
                best_text = c
        return (best_text if best_score >= 0.15 else None), float(min(max(best_score, 0.0), 1.0))

    query_embedding = _get_embedding(query)
    scored = []

    for entry in kb:
        score = _cosine_similarity(query_embedding, entry["embedding"])
        scored.append((entry["text"], score))

    scored.sort(key=lambda x: x[1], reverse=True)
    best_text, best_score = scored[0]

    # Only return a match if it exceeds the minimum relevance threshold
    if best_score < 0.5:
        return None, best_score

    return best_text, best_score
