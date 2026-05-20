"""
Natural language response generation using OpenAI.
Formats DB data and KB context into friendly, concise replies.
Spec Reference: Section 6.7
"""
import json
from openai import OpenAI
from backend.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

RESPONSE_SYSTEM_PROMPT = """You are a friendly, professional customer support assistant for BookLeaf Publishing.
Write a short, warm reply (2-4 sentences maximum) that directly answers the author question.

Rules:
- NEVER mention internal field names (author_id, uuid, database columns, etc.)
- Use natural language — no jargon
- If the data shows the book is not live yet, be encouraging
- If royalty is on_hold, be empathetic and suggest they contact support
- If answering from general policy (no DB data), still be specific and helpful
- Always end with an offer to help further if needed
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
        user_message: Original raw query from the author
        db_data: Output dict from data_retriever.fetch_author_and_books()
        kb_context: Relevant KB text chunk from search_knowledge_base()

    Returns:
        str: Natural language response (2-4 sentences, stripped)
    """
    context_parts = []

    if db_data and db_data.get("author"):
        context_parts.append(f"Author record: {json.dumps(db_data['author'])}")

    if db_data and db_data.get("books"):
        context_parts.append(f"Book(s): {json.dumps(db_data['books'])}")

    if kb_context:
        context_parts.append(f"Relevant policy information: {kb_context}")

    user_content = f'The author asked: "{user_message}"\n\n'
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
