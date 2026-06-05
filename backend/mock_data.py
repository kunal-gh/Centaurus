from __future__ import annotations

from datetime import date
from typing import Any, Dict, List
from uuid import uuid4


def _uuid(seed: str) -> str:
    """
    Stable-ish UUIDs for mock records.
    We keep them deterministic for demos and tests.
    """
    # Not a real UUIDv5 implementation; good enough for local mock mode.
    # Ensures consistent IDs across a single process run.
    return str(uuid4())


def load_mock_tables() -> Dict[str, List[Dict[str, Any]]]:
    """
    In-memory mock data aligned with `supabase/seed.sql`.
    Used when external keys are missing or OPENAI_API_KEY is 'test'.
    """
    authors = [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "email": "sara.johnson@xyz.com",
            "phone": "+919876543210",
            "dashboard_name": "Sara J.",
            "instagram_handle": "@sarapoetry23",
        },
        {
            "id": "00000000-0000-0000-0000-000000000002",
            "email": "arjun.mehta@gmail.com",
            "phone": "+919988776655",
            "dashboard_name": "Arjun Mehta",
            "instagram_handle": "@arjunwrites",
        },
        {
            "id": "00000000-0000-0000-0000-000000000003",
            "email": "priya.sharma@yahoo.com",
            "phone": "+918877665544",
            "dashboard_name": "Priya S.",
            "instagram_handle": "@priyabooks",
        },
        {
            "id": "00000000-0000-0000-0000-000000000004",
            "email": "rahul.das@outlook.com",
            "phone": "+917766554433",
            "dashboard_name": "Rahul Das",
            "instagram_handle": "@rahul_author",
        },
        {
            "id": "00000000-0000-0000-0000-000000000005",
            "email": "nisha.patel@hotmail.com",
            "phone": "+916655443322",
            "dashboard_name": "Nisha P.",
            "instagram_handle": "@nishapoems",
        },
        {
            "id": "00000000-0000-0000-0000-000000000006",
            "email": "vikram.nair@gmail.com",
            "phone": "+915544332211",
            "dashboard_name": "Vikram Nair",
            "instagram_handle": "@vikramstories",
        },
    ]

    books = [
        {
            "id": "10000000-0000-0000-0000-000000000001",
            "author_id": "00000000-0000-0000-0000-000000000001",
            "book_title": "Echoes of Srinagar",
            "isbn": "978-81-000001-1",
            "final_submission_date": str(date(2025, 10, 15)),
            "book_live_date": str(date(2025, 11, 20)),
            "royalty_status": "processing",
            "add_on_services": ["Launch Sprint", "Media Relay"],
            "sales_count": 1240,
            "author_copy_dispatched": True,
            "author_copy_dispatch_date": str(date(2025, 11, 25)),
        },
        {
            "id": "10000000-0000-0000-0000-000000000002",
            "author_id": "00000000-0000-0000-0000-000000000002",
            "book_title": "The Algorithm of Stars",
            "isbn": "978-81-000002-2",
            "final_submission_date": str(date(2025, 12, 1)),
            "book_live_date": None,
            "royalty_status": "pending",
            "add_on_services": [],
            "sales_count": 0,
            "author_copy_dispatched": False,
            "author_copy_dispatch_date": None,
        },
        {
            "id": "10000000-0000-0000-0000-000000000003",
            "author_id": "00000000-0000-0000-0000-000000000003",
            "book_title": "Letters to Nobody",
            "isbn": "978-81-000003-3",
            "final_submission_date": str(date(2025, 9, 1)),
            "book_live_date": str(date(2025, 10, 5)),
            "royalty_status": "paid",
            "add_on_services": ["Awards Circuit"],
            "sales_count": 340,
            "author_copy_dispatched": False,
            "author_copy_dispatch_date": None,
        },
        {
            "id": "10000000-0000-0000-0000-000000000004",
            "author_id": "00000000-0000-0000-0000-000000000004",
            "book_title": "Monsoon Diaries",
            "isbn": "978-81-000004-4",
            "final_submission_date": str(date(2025, 8, 10)),
            "book_live_date": str(date(2025, 9, 15)),
            "royalty_status": "on_hold",
            "add_on_services": ["Launch Sprint"],
            "sales_count": 876,
            "author_copy_dispatched": True,
            "author_copy_dispatch_date": str(date(2025, 9, 20)),
        },
        {
            "id": "10000000-0000-0000-0000-000000000005",
            "author_id": "00000000-0000-0000-0000-000000000005",
            "book_title": "Crimson Petals",
            "isbn": "978-81-000005-5",
            "final_submission_date": str(date(2025, 11, 1)),
            "book_live_date": str(date(2025, 12, 10)),
            "royalty_status": "processing",
            "add_on_services": [],
            "sales_count": 90,
            "author_copy_dispatched": False,
            "author_copy_dispatch_date": None,
        },
        {
            "id": "10000000-0000-0000-0000-000000000006",
            "author_id": "00000000-0000-0000-0000-000000000005",
            "book_title": "Violet Hours",
            "isbn": "978-81-000006-6",
            "final_submission_date": str(date(2025, 7, 15)),
            "book_live_date": str(date(2025, 8, 20)),
            "royalty_status": "paid",
            "add_on_services": ["Media Relay"],
            "sales_count": 520,
            "author_copy_dispatched": True,
            "author_copy_dispatch_date": str(date(2025, 8, 25)),
        },
        {
            "id": "10000000-0000-0000-0000-000000000007",
            "author_id": "00000000-0000-0000-0000-000000000006",
            "book_title": "Tides of Coromandel",
            "isbn": "978-81-000007-7",
            "final_submission_date": str(date(2026, 1, 10)),
            "book_live_date": None,
            "royalty_status": "pending",
            "add_on_services": ["Launch Sprint", "Awards Circuit"],
            "sales_count": 0,
            "author_copy_dispatched": False,
            "author_copy_dispatch_date": None,
        },
    ]

    # Minimal KB rows; in mock mode we prefer markdown KB + keyword search, but keep the table aligned.
    knowledge_base = [
        {
            "id": "20000000-0000-0000-0000-000000000001",
            "category": "timeline",
            "question": "How long does publishing take?",
            "answer": "After final manuscript submission, the standard publishing timeline is 45 to 60 days.",
        },
        {
            "id": "20000000-0000-0000-0000-000000000002",
            "category": "dashboard",
            "question": "How do I access my dashboard?",
            "answer": "Use the Centaurus workspace link sent during onboarding and sign in with your registered email.",
        },
    ]

    return {
        "authors": authors,
        "books": books,
        "query_logs": [],
        "identity_mappings": [],
        "knowledge_base": knowledge_base,
    }
