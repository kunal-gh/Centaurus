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
    
    print(f"Fetched {len(authors)} authors and {len(books)} books.")
    
    driver = get_driver()
    if not driver:
        print("Neo4j driver is not available. Please check NEO4J_URI configuration.")
        return

    print("Syncing nodes to Neo4j...")
    with driver.session() as session:
        # 1. Sync Authors
        for author in authors:
            session.run("""
            MERGE (a:Author {id: $id})
            SET a.email = $email,
                a.dashboard_name = $dashboard_name,
                a.instagram_handle = $instagram_handle
            """, **author)
            
        # 2. Sync Books and WROTE edges
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
                
    print("Graph synchronization complete.")

if __name__ == "__main__":
    sync_to_graph()
