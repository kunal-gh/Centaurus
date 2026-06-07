"""
Neo4j Graph Synchronization Script.

Reads the relational data from Supabase (Authors, Books) and builds the
corresponding Graph structure in Neo4j:
- Nodes: Author, Book, AddonService
- Edges: :WROTE, :HAS_ADDON
"""
import os
import sys
from dotenv import load_dotenv

# Load env variables from root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from backend.database import get_supabase
from backend.services.graph_retriever import get_driver

def sync_to_graph():
    """
    One-way sync from Supabase SQL -> Neo4j Graph.
    Uses MERGE to achieve idempotency.
    """
    print("Connecting to Supabase to fetch canonical data...")
    supabase = get_supabase()
    
    authors = supabase.table("authors").select("*").execute().data
    books = supabase.table("books").select("*").execute().data
    editors = supabase.table("editors").select("*").execute().data
    campaigns = supabase.table("campaigns").select("*").execute().data
    invoices = supabase.table("invoices").select("*").execute().data
    support_tickets = supabase.table("support_tickets").select("*").execute().data
    policy_documents = supabase.table("policy_documents").select("*").execute().data
    user_preferences = supabase.table("user_preferences").select("*").execute().data
    
    print(f"Fetched: {len(authors)} authors, {len(books)} books, {len(editors)} editors, "
          f"{len(campaigns)} campaigns, {len(invoices)} invoices, {len(support_tickets)} tickets, "
          f"{len(policy_documents)} policies, {len(user_preferences)} preferences.")
    
    driver = get_driver()
    if not driver:
        print("Neo4j driver is not available. Please check NEO4J_URI configuration.")
        return
 
    print("Syncing nodes and edges to Neo4j...")
    with driver.session() as session:
        # 1. Sync Authors
        for author in authors:
            session.run("""
            MERGE (a:Author {id: $id})
            SET a.email = $email,
                a.dashboard_name = $dashboard_name,
                a.instagram_handle = $instagram_handle
            """, **author)
            
        # 2. Sync Editors
        for editor in editors:
            session.run("""
            MERGE (e:Editor {id: $id})
            SET e.name = $name,
                e.department = $department
            """, **editor)

        # 3. Sync Books and WROTE edges
        for book in books:
            author_id = book.pop("author_id", None)
            addons = book.pop("add_on_services", [])
            
            # Create Book node
            session.run("""
            MERGE (b:Book {id: $id})
            SET b.title = $book_title,
                b.isbn = $isbn,
                b.royalty_status = $royalty_status,
                b.sales_count = $sales_count
            """, **book)
            
            # Link Author -> WROTE -> Book
            if author_id:
                session.run("""
                MATCH (a:Author {id: $author_id})
                MATCH (b:Book {id: $book_id})
                MERGE (a)-[:WROTE]->(b)
                """, author_id=author_id, book_id=book["id"])
                
            # Create Addons and link Book -> HAS_ADDON -> AddonService
            for addon_name in addons:
                session.run("""
                MATCH (b:Book {id: $book_id})
                MERGE (s:AddonService {name: $addon_name})
                MERGE (b)-[:HAS_ADDON]->(s)
                """, book_id=book["id"], addon_name=addon_name)

        # 4. Sync Campaigns and link Book -> HAS_CAMPAIGN -> Campaign
        for campaign in campaigns:
            book_id = campaign.pop("book_id", None)
            session.run("""
            MERGE (c:Campaign {id: $id})
            SET c.name = $name,
                c.budget = $budget,
                c.start_date = $start_date,
                c.end_date = $end_date
            """, **campaign)
            
            if book_id:
                session.run("""
                MATCH (b:Book {id: $book_id})
                MATCH (c:Campaign {id: $campaign_id})
                MERGE (b)-[:HAS_CAMPAIGN]->(c)
                """, book_id=book_id, campaign_id=campaign["id"])

        # 5. Sync Invoices and link Invoice -> APPROVED_BY -> Author (Reviewer)
        for invoice in invoices:
            reviewer_id = invoice.pop("reviewer_id", None)
            session.run("""
            MERGE (i:Invoice {id: $id})
            SET i.invoice_number = $invoice_number,
                i.amount = $amount,
                i.status = $status
            """, **invoice)
            
            if reviewer_id:
                session.run("""
                MATCH (i:Invoice {id: $invoice_id})
                MATCH (a:Author {id: $reviewer_id})
                MERGE (i)-[:APPROVED_BY]->(a)
                """, invoice_id=invoice["id"], reviewer_id=reviewer_id)

        # 6. Sync Support Tickets and link Ticket -> FOR_AUTHOR -> Author
        for ticket in support_tickets:
            author_id = ticket.pop("author_id", None)
            session.run("""
            MERGE (t:SupportTicket {id: $id})
            SET t.ticket_id = $ticket_id,
                t.status = $status,
                t.priority = $priority,
                t.description = $description
            """, **ticket)
            
            if author_id:
                session.run("""
                MATCH (t:SupportTicket {id: $ticket_id})
                MATCH (a:Author {id: $author_id})
                MERGE (t)-[:FOR_AUTHOR]->(a)
                """, ticket_id=ticket["id"], author_id=author_id)

        # 7. Sync Policy Documents and link Policy -> MANAGED_BY -> Editor
        for policy in policy_documents:
            owner_editor_id = policy.pop("owner_editor_id", None)
            
            # Format date to string for Neo4j compatibility
            last_verified = policy.pop("last_verified_at", None)
            if last_verified and not isinstance(last_verified, str):
                last_verified = last_verified.isoformat()
            
            session.run("""
            MERGE (p:PolicyDocument {id: $id})
            SET p.title = $title,
                p.section = $section,
                p.content = $content,
                p.version = $version,
                p.approval_status = $approval_status,
                p.last_verified_at = $last_verified
            """, last_verified=last_verified, **policy)
            
            if owner_editor_id:
                session.run("""
                MATCH (p:PolicyDocument {id: $policy_id})
                MATCH (e:Editor {id: $editor_id})
                MERGE (p)-[:MANAGED_BY]->(e)
                """, policy_id=policy["id"], editor_id=owner_editor_id)

        # 8. Sync User Preferences and link Author -> HAS_PREFERENCES -> UserPreference
        for pref in user_preferences:
            author_id = pref.pop("author_id", None)
            session.run("""
            MERGE (u:UserPreference {id: $id})
            SET u.communication_style = $communication_style,
                u.tone = $tone,
                u.max_response_length = $max_response_length,
                u.verified_user = $verified_user
            """, **pref)
            
            if author_id:
                session.run("""
                MATCH (a:Author {id: $author_id})
                MATCH (u:UserPreference {id: $pref_id})
                MERGE (a)-[:HAS_PREFERENCES]->(u)
                """, author_id=author_id, pref_id=pref["id"])

    print("Graph synchronization complete.")

if __name__ == "__main__":
    sync_to_graph()

