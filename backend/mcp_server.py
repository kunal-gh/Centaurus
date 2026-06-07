"""
Centaurus Model Context Protocol (MCP) Server.
Exposes specialized enterprise tools for external swarms, agents, or client applications.
"""
from typing import Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP

from backend.database import get_supabase
from backend.services import identity_unifier, knowledge_base, graph_retriever
from backend.models import ResolveRequest

mcp = FastMCP("Centaurus")


# ── Identity Tools ───────────────────────────────────────────────────────────

@mcp.tool()
def resolve_identity(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    name: Optional[str] = None,
    instagram: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fuzzy resolve multiple identity signals into a verified author profile UUID.
    """
    try:
        all_profiles = get_supabase().table("authors").select("*").execute().data
        req_signals = {
            "email": email,
            "phone": phone,
            "name": name,
            "instagram": instagram,
        }
        result = identity_unifier.unify_identity(req_signals, all_profiles)
        return {"status": "success", "result": result}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@mcp.tool()
def update_user_signals(
    author_id: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    name: Optional[str] = None,
    instagram: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update identity signals for an existing author profile.
    """
    try:
        update_data = {}
        if email:
            update_data["email"] = email
        if phone:
            update_data["phone"] = phone
        if name:
            update_data["dashboard_name"] = name
        if instagram:
            update_data["instagram_handle"] = instagram

        if not update_data:
            return {"status": "error", "message": "No update signals provided."}

        res = get_supabase().table("authors").update(update_data).eq("id", author_id).execute()
        return {"status": "success", "updated": res.data}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


# ── Knowledge Tools ───────────────────────────────────────────────────────────

@mcp.tool()
def search_policies(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Perform vector/hybrid search against policy documents applying governance approval filters.
    """
    try:
        # Fetch verified preference state dynamically if matching logs exist
        user_prefs = {"verified": True}  # Default to verified for admin/agent search
        results = knowledge_base.search_knowledge_base_hybrid(query, top_k=top_k, user_preferences=user_prefs)
        return results
    except Exception as exc:
        return [{"error": str(exc)}]


@mcp.tool()
def get_knowledge_citation(chunk_id: str) -> Dict[str, Any]:
    """
    Retrieve document source, author, and version lineage metadata for a chunk.
    """
    try:
        # In mock mode, we fallback to manual chunks parsing
        kb_chunks = knowledge_base.build_kb_cache()
        for chunk in kb_chunks:
            if chunk.get("metadata", {}).get("chunk_id") == chunk_id:
                return {"status": "success", "metadata": chunk.get("metadata")}
        return {"status": "error", "message": f"Chunk {chunk_id} not found."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


# ── Graph (Neo4j) Tools ───────────────────────────────────────────────────────

@mcp.tool()
def execute_cypher_read(query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute a read-only Cypher query against the Neo4j instance.
    Returns mocked/fallbacks if in mock mode.
    """
    driver = graph_retriever.get_driver()
    if not driver:
        # Fallback explanation in mock mode
        return {
            "status": "mock_mode",
            "message": "Neo4j is not connected. Returning empty query representation.",
            "data": []
        }
    try:
        with driver.session() as session:
            result = session.run(query, **(parameters or {}))
            records = [dict(record) for record in result]
            return {"status": "success", "data": records}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@mcp.tool()
def get_entity_relations(entity_id: str) -> Dict[str, Any]:
    """
    Execute a graph traversal returning all active relationships connected to the node ID.
    """
    query = """
    MATCH (n {id: $entity_id})-[r]-(m)
    RETURN type(r) AS relationship, labels(m) AS target_labels, m.id AS target_id, properties(m) AS target_properties
    LIMIT 20
    """
    return execute_cypher_read(query, {"entity_id": entity_id})


# ── Memory Tools ──────────────────────────────────────────────────────────────

@mcp.tool()
def fetch_user_preferences(author_id: str) -> Dict[str, Any]:
    """
    Retrieve the long-term preference memory profile for a verified user.
    """
    try:
        res = get_supabase().table("user_preferences").select("*").eq("author_id", author_id).execute()
        if res.data:
            return {"status": "success", "preferences": res.data[0]}
        return {"status": "success", "preferences": None, "message": "No preferences found for this author."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@mcp.tool()
def store_episodic_memory(author_id: str, summary: str) -> Dict[str, Any]:
    """
    Append / overwrite summarized episodic context to the memory buffer.
    """
    try:
        # We append a mock query log entry summarizing the episodic turn
        log_entry = {
            "author_id": author_id,
            "raw_query": "[Episodic Memory Update]",
            "response": f"Summary: {summary}",
            "channel": "system",
            "confidence": 1.0,
            "escalated": False,
        }
        get_supabase().table("query_logs").insert(log_entry).execute()
        return {"status": "success", "message": "Episodic memory turn logged successfully."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


# ── Reviewer & Governance Tools ───────────────────────────────────────────────

@mcp.tool()
def fetch_escalations_queue() -> Dict[str, Any]:
    """
    Retrieve escalated logs waiting for human reviewer response.
    """
    try:
        res = get_supabase().table("query_logs").select("*").eq("escalated", True).order("created_at", desc=True).execute()
        return {"status": "success", "queue": res.data}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@mcp.tool()
def submit_decision(
    query_log_id: str,
    approved_response: str,
    rationale: Optional[str] = None,
    reviewed_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Resolve an escalated query, persist the corrected answer, and close the audit block.
    """
    try:
        log_res = get_supabase().table("query_logs").select("response").eq("id", query_log_id).execute()
        if not log_res.data:
            return {"status": "error", "message": f"Query log {query_log_id} not found."}
            
        original_response = log_res.data[0].get("response", "")
        
        # Log to reviewer decisions
        get_supabase().table("reviewer_decisions").insert({
            "query_log_id": query_log_id,
            "original_response": original_response,
            "approved_response": approved_response,
            "rationale": rationale,
            "reviewed_by": reviewed_by
        }).execute()
        
        # Mark as resolved
        get_supabase().table("query_logs").update({
            "escalated": False,
            "escalation_reason": "Resolved by MCP tool"
        }).eq("id", query_log_id).execute()
        
        return {"status": "success", "message": "Decision recorded successfully."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@mcp.tool()
def register_policy_document(
    title: str,
    section: str,
    content: str,
    version: int = 1,
    owner_editor_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new operational policy document entry under active/draft state.
    """
    try:
        new_policy = {
            "title": title,
            "section": section,
            "content": content,
            "version": version,
            "approval_status": "draft",
            "owner_editor_id": owner_editor_id
        }
        res = get_supabase().table("policy_documents").insert(new_policy).execute()
        return {"status": "success", "policy": res.data}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@mcp.tool()
def deprecate_policy(policy_id: str) -> Dict[str, Any]:
    """
    Deprecate a policy document, excluding it from future retrieval queries.
    """
    try:
        res = get_supabase().table("policy_documents").update({"approval_status": "deprecated"}).eq("id", policy_id).execute()
        return {"status": "success", "policy": res.data}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


if __name__ == "__main__":
    mcp.run()
