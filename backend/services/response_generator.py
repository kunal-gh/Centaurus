"""
Natural language response generation using OpenAI.
Formats record data and retrieval context into concise replies.
"""
import json
from openai import OpenAI
from backend.config import settings

client = None if settings.is_mock_mode else OpenAI(api_key=settings.OPENAI_API_KEY)

RESPONSE_SYSTEM_PROMPT = """You are Centaurus, a calm and professional publishing operations copilot.
Write a short, direct reply (2-4 sentences maximum) that answers the user's question clearly.

Rules:
- NEVER mention internal field names (author_id, uuid, database columns, etc.)
- Use natural language - no jargon
- If the data shows the book is not live yet, be encouraging
- If royalty is on_hold, be empathetic and suggest they contact support
- If answering from general policy (no DB data), still be specific and helpful
- End with a clear next step or offer of further help when appropriate
- If the query was escalated, use the exact escalation message provided; do not rewrite it"""


def generate_response(
    intent: str,
    user_message: str,
    db_data: dict = None,
    kb_context: str = None
) -> str:
    """
    Generates a conversational response from structured data.

    Args:
        intent: Classified intent string from intent_classifier
        user_message: Original raw query from the user
        db_data: Output dict from data_retriever.fetch_author_and_books()
        kb_context: Relevant KB text chunk from search_knowledge_base()

    Returns:
        str: Natural language response (2-4 sentences, stripped)
    """
    # Mock mode: deterministic, template-based responses.
    if settings.is_mock_mode:
        book = None
        if db_data and db_data.get("books"):
            book = db_data["books"][0]
        if kb_context:
            return f"{kb_context.strip()}\n\nIf you’d like, share your registered email and I can also check your record-level status."
        if not book:
            return "I couldn’t find a matching record with the details provided. Share your registered email or phone number and I can check the status directly."

        title = book.get("book_title", "your book")
        if intent == "publishing_timeline":
            live = book.get("book_live_date")
            if live:
                return f"Good news - **{title}** is live as of {live}. If you want, I can also share author copy and service-program status."
            return f"Thanks for checking in. **{title}** isn’t marked live yet. If you share your latest submission date, I can help estimate the remaining timeline."
        if intent == "royalty_status":
            status = book.get("royalty_status", "pending")
            return f"Your royalty status for **{title}** is currently **{status}**. If you want, I can help you with next steps based on that status."
        if intent == "addon_status":
            addons = book.get("add_on_services") or []
            addons_text = ", ".join(addons) if addons else "no service programs"
            return f"For **{title}**, I can see **{addons_text}** on your account. Want me to explain what each service program covers and the usual timeline?"
        if intent == "author_copy":
            dispatched = bool(book.get("author_copy_dispatched"))
            when = book.get("author_copy_dispatch_date")
            if dispatched:
                return f"Your author copy for **{title}** was dispatched on {when or 'a recent date'}. If you share your city, I can estimate delivery timing."
            return f"Your author copy for **{title}** isn’t marked as dispatched yet. Typically, copies go out within 7-10 business days of the book going live."
        if intent == "book_sales":
            sales = book.get("sales_count", 0)
            return f"Your current recorded sales count for **{title}** is **{sales}**. If you want, I can explain how often sales data updates and where to view it."
        return "I can help with timelines, royalties, workspace access, service programs, author copies, and sales. Tell me which one you’d like to check."

    context_parts = []

    if db_data and db_data.get("author"):
        context_parts.append(f"Author record: {json.dumps(db_data['author'])}")

    if db_data and db_data.get("books"):
        context_parts.append(f"Book(s): {json.dumps(db_data['books'])}")

    if kb_context:
        context_parts.append(f"Relevant policy information: {kb_context}")

    user_content = f'The user asked: "{user_message}"\n\n'
    if context_parts:
        user_content += "Available data:\n" + "\n".join(context_parts)
    else:
        user_content += "No specific author data was found."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": RESPONSE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        temperature=0.4,
        max_tokens=250
    )

    return response.choices[0].message.content.strip()
