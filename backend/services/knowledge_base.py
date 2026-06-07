"""
RAG pipeline using OpenAI embeddings and NumPy cosine similarity.
In-memory only. No external vector database required for MVP.
Spec Reference: Section 6.6
"""
import os
import json
import traceback
from typing import List, Dict, Any
from backend.config import settings
from backend.services.retrievers import qdrant_retriever
from backend.services.retrievers.chunker import chunk_markdown_file

# Global in-memory cache for mock mode
_KB_ENTRIES = None


def _chunk_markdown(file_path: str = "knowledge_base/centaurus_ops_manual.md") -> list:
    """
    Fallback mock-mode chunker that reads raw sections from the manual.
    """
    chunks = chunk_markdown_file(file_path)
    return [c.dict() for c in chunks]


def build_kb_cache(
    file_path: str = "knowledge_base/centaurus_ops_manual.md",
    cache_path: str = "knowledge_base/kb_embeddings.json"
) -> list:
    """
    Initializes retrieval storage.
    In mock mode: loads raw chunks into an in-memory cache.
    In live mode: initializes the local Qdrant collection and indexes the manual.
    """
    global _KB_ENTRIES

    if settings.is_mock_mode:
        if _KB_ENTRIES is not None:
            return _KB_ENTRIES
        _KB_ENTRIES = _chunk_markdown(file_path)
        return _KB_ENTRIES

    # Live Mode: Initialize Qdrant Hybrid Collection
    try:
        qdrant_retriever.init_collection(force_recreate=False)
    except Exception as exc:
        print(f"Error initializing Qdrant collection: {exc}. Falling back to in-memory mock mode.")
        settings.is_mock_mode = True
        _KB_ENTRIES = _chunk_markdown(file_path)
        return _KB_ENTRIES

    return []


def search_knowledge_base_hybrid(query: str, top_k: int = 3, user_preferences: dict = None) -> List[Dict[str, Any]]:
    """
    Performs a hybrid search and applies Knowledge Governance filter rules:
    - Excludes policies with approval_status = 'deprecated'
    - Restricts approval_status in ('draft', 'pending_approval') to verified users
    - Injects data lineage citations (version, editor owner) into metadata
    """
    build_kb_cache()

    raw_results = []
    if settings.is_mock_mode:
        q = (query or "").lower()
        q_terms = {t for t in q.replace("?", " ").replace(".", " ").split() if len(t) > 2}
        scored_entries = []

        kb = _KB_ENTRIES or []
        for entry in kb:
            text = entry["text"]
            text_terms = {t for t in text.lower().replace("?", " ").replace(".", " ").split() if len(t) > 2}
            overlap = len(q_terms & text_terms) if q_terms else 0
            score = overlap / max(len(q_terms), 1)

            if score >= 0.15:
                scored_entries.append({
                    "text": text,
                    "score": float(score),
                    "metadata": dict(entry["metadata"])
                })

        scored_entries.sort(key=lambda x: x["score"], reverse=True)
        raw_results = scored_entries[:top_k]
    else:
        # Live hybrid vector search in Qdrant
        raw_results = qdrant_retriever.search_hybrid(query, top_k=top_k)

    # ── Knowledge Governance Filters ──
    from backend.database import get_supabase
    
    is_verified = False
    if user_preferences and user_preferences.get("verified"):
        is_verified = True
        
    try:
        policies = get_supabase().table("policy_documents").select("*, editors(name)").execute().data
    except Exception:
        policies = []

    # Map policy records by their section tag
    policy_map = {p["section"].lower(): p for p in policies}

    filtered_results = []
    for res in raw_results:
        metadata = res.get("metadata", {})
        section_tag = metadata.get("section", "").lower()
        
        # Check against database governance
        policy = policy_map.get(section_tag)
        if policy:
            status = policy.get("approval_status", "approved")
            version = policy.get("version", 1)
            owner = policy.get("editors", {}).get("name", "System")
            
            # Rule 1: Exclude deprecated policies
            if status == "deprecated":
                continue
                
            # Rule 2: Limit draft/pending policies to verified users
            if status in ("draft", "pending_approval") and not is_verified:
                continue
                
            # Rule 3: Append version and owner provenance to metadata for citation logging
            metadata["version"] = version
            metadata["owner"] = owner
            metadata["approval_status"] = status
            
            # Prepend a warning badge to the text if it is draft
            if status in ("draft", "pending_approval"):
                res["text"] = f"[DRAFT POLICY - INTERNAL USE ONLY]\n{res['text']}"
        
        filtered_results.append(res)
        
    return filtered_results[:top_k]


def search_knowledge_base(query: str, top_k: int = 1) -> tuple:
    """
    Retrieves the best match for backwards compatibility with the linear main pipeline.
    Returns:
        Tuple (best_text, best_score)
    """
    results = search_knowledge_base_hybrid(query, top_k=top_k)
    if not results:
        return None, 0.0

    best_match = results[0]
    return best_match["text"], best_match["score"]

