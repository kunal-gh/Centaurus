"""
Centaurus Graph Retriever (Wave 3).
Executes Cypher queries against Neo4j to retrieve complex, multi-hop
relationships that standard vector search struggles with (e.g.,
Author -> Book -> Contract -> RoyaltyEvent).
"""
import os
import traceback
from typing import Dict, Any, List, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

from backend.config import settings

_DRIVER = None


def get_driver():
    """
    Lazy-loads the Neo4j driver singleton.
    """
    global _DRIVER
    if _DRIVER is None:
        if settings.is_mock_mode:
            return None
        
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        
        try:
            # Short timeout so it fails fast if Neo4j is not running
            _DRIVER = GraphDatabase.driver(uri, auth=(user, password), connection_timeout=2.0)
            # Verify connectivity
            _DRIVER.verify_connectivity()
            print(f"[GraphRAG] Connected to Neo4j at {uri}")
        except Exception as e:
            print(f"[GraphRAG] Warning: Could not connect to Neo4j: {e}. Graph queries disabled.")
            _DRIVER = None
            
    return _DRIVER


def get_author_publishing_context(author_id: str) -> Optional[Dict[str, Any]]:
    """
    2-Hop Graph Traversal: Author -> Book -> Addons & Royalties.
    Returns a unified context document detailing the author's entire publishing landscape.
    """
    if settings.is_mock_mode:
        return {"mock": True, "note": "GraphRAG disabled in mock mode."}
        
    driver = get_driver()
    if not driver:
        return None

    query = """
    MATCH (a:Author {id: $author_id})
    OPTIONAL MATCH (a)-[:WROTE]->(b:Book)
    OPTIONAL MATCH (b)-[:HAS_ADDON]->(addon:AddonService)
    RETURN 
        a.dashboard_name AS author_name,
        a.email AS author_email,
        collect(DISTINCT {
            id: b.id,
            title: b.title,
            status: b.royalty_status,
            sales: b.sales_count,
            addons: [(b)-[:HAS_ADDON]->(s) | s.name]
        }) AS books
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, author_id=author_id).single()
            if result:
                return dict(result)
            return None
    except Exception as exc:
        print(f"[GraphRAG] Query failed: {exc}")
        return None


def extract_graph_context_for_query(intent: str, author_id: Optional[str]) -> str:
    """
    High-level orchestrator. Given an intent and author_id, fetches the relevant
    graph sub-tree and formats it as text to inject into the LLM prompt.
    """
    if not author_id:
        return ""
        
    # Only fetch graph context for entity-heavy operational intents
    if intent not in ["publishing_timeline", "royalty_status", "book_sales", "addon_status"]:
        return ""
        
    context_data = get_author_publishing_context(author_id)
    if not context_data:
        return ""
        
    if context_data.get("mock"):
        return ""
        
    # Format the graph data into English text for the LLM
    author_name = context_data.get("author_name", "Author")
    books = context_data.get("books", [])
    
    lines = [f"[Graph Knowledge Base: Author Landscape for {author_name}]"]
    for b in books:
        if b.get('title'):
            lines.append(f"- Book: '{b['title']}'")
            lines.append(f"  Sales: {b.get('sales', 0)}")
            lines.append(f"  Royalty Status: {b.get('status', 'unknown')}")
            addons = b.get('addons', [])
            if addons:
                lines.append(f"  Active Addons: {', '.join(addons)}")
    
    return "\n".join(lines)
