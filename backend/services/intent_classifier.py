"""
Intent classification using OpenAI JSON mode.
Extracts: intent, entities (email, book_title, isbn, add_on_name), confidence, query_type.
Spec Reference: Section 6.4
"""
import json
import re
from openai import OpenAI
from backend.config import settings

client = None if settings.is_mock_mode else OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """You are an intent extractor for BookLeaf Publishing support system.

Analyze the user message and return STRICT JSON with this exact structure:
{
  "intent": "<one of allowed intents>",
  "entities": {
    "email": "<email if mentioned, else null>",
    "book_title": "<book title if mentioned, else null>",
    "isbn": "<ISBN if mentioned, else null>",
    "add_on_name": "<add-on name if mentioned, else null>"
  },
  "confidence": <float between 0.0 and 1.0>,
  "query_type": "<db_query or kb_query>"
}

Allowed intents:
- publishing_timeline   (asking about book live date, when book will launch, how long)
- royalty_status        (asking about royalty, earnings, payment, when paid)
- dashboard_access      (asking about login, dashboard, account access, forgot password)
- addon_status          (asking about Bestseller Package, PR Push, Award Submission)
- author_copy           (asking about physical copy, delivery, dispatch, tracking)
- book_sales            (asking about sales numbers, how many copies sold, revenue)
- general_faq           (general publishing policy question not tied to a specific record)
- escalate_human        (angry, threatening, requesting refund, mentions legal action, complaint)
- unknown               (cannot determine what the user wants)

Rules:
- confidence < 0.7 for vague or ambiguous messages
- confidence < 0.5 for very unclear messages
- query_type = "db_query" when the answer requires looking up a specific author record (email/name/book mentioned)
- query_type = "kb_query" when the answer is a general policy/process question (no specific identifier)
- If unsure between db_query and kb_query, prefer db_query if any identifier exists
- If the user is angry or uses words like "lawyer", "unacceptable", "refund", "sue", intent MUST be "escalate_human"

Return ONLY valid JSON. No prose, no markdown, no explanation outside the JSON object."""


def classify_query(user_message: str) -> dict:
    """
    Classifies user message into intent and extracts entities.

    Args:
        user_message: Raw natural language query

    Returns:
        dict with keys: intent, entities, confidence, query_type
    """
    # Mock mode: heuristic classifier keeps demo runnable without external keys.
    if settings.is_mock_mode:
        msg = (user_message or "").lower()
        if any(w in msg for w in ["lawyer", "legal", "sue", "refund", "unacceptable", "complaint"]):
            return {"intent": "escalate_human", "entities": {"email": None, "book_title": None, "isbn": None, "add_on_name": None}, "confidence": 0.99, "query_type": "db_query"}
        email_match = re.search(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", msg)
        entities = {"email": email_match.group(0) if email_match else None, "book_title": None, "isbn": None, "add_on_name": None}

        def _intent(intent: str, conf: float, qt: str):
            return {"intent": intent, "entities": entities, "confidence": conf, "query_type": qt}

        if any(w in msg for w in ["royalty", "earning", "payment"]):
            return _intent("royalty_status", 0.9, "db_query" if entities["email"] else "kb_query")
        if any(w in msg for w in ["dashboard", "login", "password", "access"]):
            return _intent("dashboard_access", 0.9, "kb_query")
        if any(w in msg for w in ["bestseller", "pr push", "award", "add-on", "addon"]):
            return _intent("addon_status", 0.9, "db_query" if entities["email"] else "kb_query")
        if any(w in msg for w in ["author copy", "physical copy", "dispatch", "tracking"]):
            return _intent("author_copy", 0.9, "db_query" if entities["email"] else "kb_query")
        if any(w in msg for w in ["sales", "copies sold", "sold"]):
            return _intent("book_sales", 0.9, "db_query" if entities["email"] else "kb_query")
        if ("book" in msg and "live" in msg) or any(
            w in msg for w in ["timeline", "how long", "go live", "live date", "launch"]
        ):
            # 0.90 triggers confidence_scorer "clear-case" floor when identity is strong and kb_relevance ~ 0.
            return _intent("publishing_timeline", 0.90, "db_query" if entities["email"] else "kb_query")
        if len(msg.strip()) < 6:
            return _intent("unknown", 0.3, "kb_query")
        return _intent("general_faq", 0.75, "kb_query")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=300,
    )

    result = json.loads(response.choices[0].message.content)

    # Normalize confidence to float
    result["confidence"] = float(result.get("confidence", 0.5))

    # Ensure query_type exists with sensible default
    if "query_type" not in result:
        result["query_type"] = "kb_query" if result["intent"] == "general_faq" else "db_query"

    return result
