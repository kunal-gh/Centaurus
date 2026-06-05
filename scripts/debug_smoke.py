# Core-functionality smoke check (no debug-session file logging).
# Run from: python scripts/debug_smoke.py
# Uses OPENAI_API_KEY=test + empty Supabase env → in-memory mock.

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    os.environ["OPENAI_API_KEY"] = "test"
    os.environ.setdefault("SUPABASE_URL", "")
    os.environ.setdefault("SUPABASE_KEY", "")

    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from starlette.testclient import TestClient

    from backend.main import app
    from backend.database import get_supabase

    client = TestClient(app)

    h1 = client.get("/health")
    assert h1.status_code == 200, h1.text
    assert h1.json().get("database") == "connected", h1.json()
    print("OK  /health")

    h2 = client.post(
        "/chat",
        json={
            "channel": "web",
            "message": "Is my book live yet?",
            "user_email": "sara.johnson@xyz.com",
        },
    )
    b2 = h2.json()
    assert h2.status_code == 200 and not b2.get("escalated"), b2
    assert b2.get("author_found") is True, b2
    assert b2.get("intent") == "publishing_timeline", b2
    assert float(b2.get("confidence", 0)) >= 0.8, b2
    print("OK  /chat book live + user_email (DB path, no escalation)")

    h3 = client.post("/chat", json={"channel": "web", "message": "as"})
    b3 = h3.json()
    assert h3.status_code == 200 and b3.get("escalated") is True, b3
    print("OK  /chat unknown -> escalation")

    h4 = client.post(
        "/identity/resolve",
        json={
            "email": "sara.johnson@xyz.com",
            "phone": "+91 9876543210",
            "name": "Sara J.",
            "instagram": "@sarapoetry23",
        },
    )
    b4 = h4.json()
    assert h4.status_code == 200, b4
    assert b4.get("action") == "auto_link" and b4.get("matched_author_id"), b4
    print("OK  /identity/resolve Sara demo")

    h5 = client.post(
        "/chat",
        json={
            "channel": "web",
            "message": "When will I get my royalty?",
            "user_email": "nisha.patel@hotmail.com",
        },
    )
    b5 = h5.json()
    assert h5.status_code == 200, b5
    assert b5.get("books_found") == 2, b5
    assert "multiple books" in (b5.get("response") or "").lower(), b5
    print("OK  /chat multi-book disambiguation")

    qrows = get_supabase().table("query_logs").select("*").execute().data or []
    assert len(qrows) >= 3, len(qrows)
    print("OK  query_logs persisted")

    print("\nAll core smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
