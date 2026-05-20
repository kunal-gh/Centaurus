"""
Supabase data retrieval for author and book records.
Handles: exact email match, normalized phone match, no match, multiple books, database errors.
Spec Reference: Section 6.5
"""
from backend.database import get_supabase


def normalize_phone(phone: str) -> str:
    """Strips +, spaces, dashes, and leading zeros for comparison."""
    if not phone:
        return ""
    return phone.replace("+", "").replace(" ", "").replace("-", "").lstrip("0")


def fetch_author_and_books(email: str = None, phone: str = None) -> dict:
    """
    Retrieves author record and all linked books from Supabase.

    Args:
        email: Exact email address (preferred identifier)
        phone: Phone number (will be normalized for comparison)

    Returns:
        dict with keys:
        - author: author row dict or None
        - books: list of book row dicts or empty list
        - error_flags: list of error strings (e.g. DB_ERROR)
        - match_confidence: 1.0 if found, 0.0 if not
        - multiple_books: bool (True if author has > 1 book)
    """
    supabase = get_supabase()
    error_flags = []
    author = None
    books = []

    try:
        if email:
            # Exact email match — primary and fastest lookup
            result = supabase.table("authors").select("*").eq("email", email).execute()
            if result.data:
                author = result.data[0]

        elif phone:
            # Normalized phone match — fetch all and filter in Python
            # (avoids SQL-level normalization complexity)
            normalized_input = normalize_phone(phone)
            result = supabase.table("authors").select("*").execute()
            for row in result.data:
                if normalize_phone(row.get("phone", "")) == normalized_input:
                    author = row
                    break

        if author:
            book_result = supabase.table("books").select("*").eq("author_id", author["id"]).execute()
            books = book_result.data or []

    except Exception as e:
        error_flags.append(f"DB_ERROR: {str(e)}")

    return {
        "author": author,
        "books": books,
        "error_flags": error_flags,
        "match_confidence": 1.0 if author else 0.0,
        "multiple_books": len(books) > 1
    }
