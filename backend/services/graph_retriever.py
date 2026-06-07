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
    Multi-Hop Graph Traversal: Author -> Book -> Addons, Campaigns, Invoices, Tickets, Preferences.
    Returns a unified context document detailing the author's entire operational landscape.
    """
    if settings.is_mock_mode:
        # High-fidelity mock GraphRAG return for the pre-seeded authors
        if author_id == "00000000-0000-0000-0000-000000000001":  # Sara Johnson
            return {
                "author_name": "Sara J.",
                "author_email": "sara.johnson@xyz.com",
                "books": [{"id": "b1", "title": "Echoes of Srinagar", "status": "processing", "sales": 1240}],
                "addons": ["Launch Sprint", "Media Relay"],
                "campaigns": [{"name": "Winter Reads Push", "budget": 1500.00, "start_date": "2025-11-20"}],
                "invoices": [{"invoice_number": "INV-2025-001", "amount": 450.00, "status": "approved"}],
                "tickets": [{"ticket_id": "TCK-1001", "status": "resolved", "priority": "medium", "description": "Cannot download royalties statement PDF"}],
                "preferences": {"style": "concise", "tone": "professional", "max_length": 500, "verified": True}
            }
        elif author_id == "00000000-0000-0000-0000-000000000003":  # Priya Sharma
            return {
                "author_name": "Priya S.",
                "author_email": "priya.sharma@yahoo.com",
                "books": [{"id": "b3", "title": "Letters to Nobody", "status": "paid", "sales": 340}],
                "addons": ["Awards Circuit"],
                "campaigns": [{"name": "Awards Campaign 2025", "budget": 2500.00, "start_date": "2025-10-05"}],
                "invoices": [{"invoice_number": "INV-2025-002", "amount": 340.00, "status": "paid"}],
                "tickets": [],
                "preferences": {"style": "formal", "tone": "helpful", "max_length": 1000, "verified": True}
            }
        else:
            return {
                "author_name": "Mock Author",
                "author_email": "mock@author.com",
                "books": [],
                "addons": [],
                "campaigns": [],
                "invoices": [],
                "tickets": [],
                "preferences": {"style": "formal", "tone": "helpful", "max_length": 1000, "verified": False}
            }
        
    driver = get_driver()
    if not driver:
        return None

    query = """
    MATCH (a:Author {id: $author_id})
    OPTIONAL MATCH (a)-[:WROTE]->(b:Book)
    OPTIONAL MATCH (b)-[:HAS_ADDON]->(addon:AddonService)
    OPTIONAL MATCH (b)-[:HAS_CAMPAIGN]->(c:Campaign)
    OPTIONAL MATCH (invoice:Invoice)-[:APPROVED_BY]->(a)
    OPTIONAL MATCH (ticket:SupportTicket)-[:FOR_AUTHOR]->(a)
    OPTIONAL MATCH (a)-[:HAS_PREFERENCES]->(pref:UserPreference)
    RETURN 
        a.dashboard_name AS author_name,
        a.email AS author_email,
        collect(DISTINCT {
            id: b.id,
            title: b.title,
            status: b.royalty_status,
            sales: b.sales_count
        }) AS books,
        collect(DISTINCT addon.name) AS addons,
        collect(DISTINCT {
            name: c.name,
            budget: c.budget,
            start_date: c.start_date
        }) AS campaigns,
        collect(DISTINCT {
            invoice_number: invoice.invoice_number,
            amount: invoice.amount,
            status: invoice.status
        }) AS invoices,
        collect(DISTINCT {
            ticket_id: ticket.ticket_id,
            status: ticket.status,
            priority: ticket.priority,
            description: ticket.description
        }) AS tickets,
        {
            style: pref.communication_style,
            tone: pref.tone,
            max_length: pref.max_response_length,
            verified: pref.verified_user
        } AS preferences
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
    record_intents = {
        "publishing_timeline", "royalty_status", "book_sales", 
        "addon_status", "dashboard_access", "author_copy"
    }
    if intent not in record_intents:
        return ""
        
    context_data = get_author_publishing_context(author_id)
    if not context_data:
        return ""
        
    # Format the graph data into English text for the LLM
    author_name = context_data.get("author_name", "Author")
    books = context_data.get("books", [])
    addons = context_data.get("addons", [])
    campaigns = context_data.get("campaigns", [])
    invoices = context_data.get("invoices", [])
    tickets = context_data.get("tickets", [])
    prefs = context_data.get("preferences", {})
    
    lines = [f"[Graph Knowledge Base: Author Landscape for {author_name}]"]
    
    # User Preferences
    if prefs and prefs.get("style"):
        lines.append(f"- Communication Settings: Style={prefs.get('style')}, Tone={prefs.get('tone')}, MaxLength={prefs.get('max_length')}, Verified={prefs.get('verified')}")
        
    # Books
    for b in books:
        if b.get('title'):
            lines.append(f"- Book: '{b['title']}' (ID: {b.get('id')})")
            lines.append(f"  Sales: {b.get('sales', 0)} units")
            lines.append(f"  Royalty Status: {b.get('status', 'unknown')}")
            
    # Addons
    if addons:
        lines.append(f"- Enrolled Addon Services: {', '.join(addons)}")
        
    # Campaigns
    for c in campaigns:
        if c.get('name'):
            lines.append(f"- Marketing Campaign: '{c['name']}' (Budget: ${c.get('budget')}, Started: {c.get('start_date')})")
            
    # Invoices
    for inv in invoices:
        if inv.get('invoice_number'):
            lines.append(f"- Invoice: {inv['invoice_number']} (Amount: ${inv.get('amount')}, Status: {inv.get('status')})")
            
    # Support Tickets
    for t in tickets:
        if t.get('ticket_id'):
            lines.append(f"- Support Ticket: {t['ticket_id']} (Status: {t.get('status')}, Priority: {t.get('priority')})")
            lines.append(f"  Issue Description: {t.get('description')}")
    
    return "\n".join(lines)

