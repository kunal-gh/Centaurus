"""
Centaurus - FastAPI control plane.

Endpoints:
  POST /chat                  -> Main answer pipeline
  POST /identity/resolve      -> Standalone identity resolution demo
  GET  /admin/identity-review -> Pending reviewer decisions
  GET  /health                -> Service and database health check
"""
import traceback
from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from backend.models import ChatRequest, ChatResponse, IdentityRequest
from backend.database import get_supabase
from backend.services import (
    intent_classifier,
    data_retriever,
    knowledge_base,
    response_generator,
    confidence_scorer,
    identity_unifier,
)


app = FastAPI(
    title="Centaurus",
    description="Knowledge worker agent foundation for publishing operations",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the browser demo UI directly from FastAPI.
app.mount("/app", StaticFiles(directory="web", html=True), name="web")


@app.get("/")
async def root():
    return RedirectResponse(url="/app/")


@app.on_event("startup")
async def startup_event():
    """
    Pre-build the knowledge cache on startup to avoid first-request latency.
    """
    knowledge_base.build_kb_cache()


def _escalate_and_log(log_entry: dict, reason: str) -> ChatResponse:
    """
    Standardized escalation handler used by all failure paths.
    """
    message = (
        "I want to make sure you get the most accurate help. "
        "I've escalated your query to a Centaurus reviewer "
        "who will respond within 24 business hours. "
        f"[Escalation reason: {reason}]"
    )

    log_entry.update({
        "escalated": True,
        "escalation_reason": reason,
        "response": message,
        "confidence": 0.0,
    })

    try:
        get_supabase().table("query_logs").insert(log_entry).execute()
    except Exception:
        pass

    return ChatResponse(
        response=message,
        confidence=0.0,
        escalated=True,
        reason=reason,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Current linear answer pipeline used by Centaurus.

    1. Intent classification
    2. Identity resolution
    3. Structured record retrieval
    4. Knowledge retrieval
    5. Confidence scoring
    6. Escalation check
    7. Response generation
    8. Audit logging
    """
    log_entry = {
        "channel": req.channel,
        "raw_query": req.message,
        "escalated": False,
    }

    try:
        intent_data = intent_classifier.classify_query(req.message)
        intent = intent_data.get("intent", "unknown")
        intent_conf = intent_data.get("confidence", 0.5)
        entities = intent_data.get("entities", {})
        query_type = intent_data.get("query_type", "kb_query")

        log_entry["intent"] = intent

        resolved_email = req.user_email or (entities.get("email") if entities else None)
        resolved_phone = req.user_phone

        record_intents = {
            "publishing_timeline",
            "royalty_status",
            "dashboard_access",
            "addon_status",
            "author_copy",
            "book_sales",
        }
        if (resolved_email or resolved_phone) and intent in record_intents and query_type == "kb_query":
            query_type = "db_query"

        identity_conf = 0.5
        author_id = None

        if resolved_email or resolved_phone or req.user_name or req.user_instagram:
            all_profiles = get_supabase().table("authors").select("*").execute().data
            identity_result = identity_unifier.unify_identity(
                {
                    "email": resolved_email,
                    "phone": resolved_phone,
                    "name": req.user_name,
                    "instagram": req.user_instagram,
                },
                all_profiles,
            )
            identity_conf = identity_result["confidence"]
            author_id = identity_result.get("matched_author_id")
            log_entry["author_id"] = author_id

            if identity_result.get("action") == "verify_manually" and author_id:
                platform_identifier = (
                    resolved_email
                    or resolved_phone
                    or req.user_instagram
                    or req.user_name
                    or "unknown"
                )
                try:
                    get_supabase().table("identity_mappings").insert({
                        "author_id": author_id,
                        "platform": req.channel,
                        "platform_identifier": platform_identifier,
                        "match_confidence": identity_conf,
                        "verified": False,
                    }).execute()
                except Exception:
                    pass

        db_result = {
            "author": None,
            "books": [],
            "error_flags": [],
            "multiple_books": False,
        }

        if query_type == "db_query" and (resolved_email or resolved_phone):
            db_result = data_retriever.fetch_author_and_books(
                email=resolved_email,
                phone=resolved_phone,
            )

            if db_result["error_flags"]:
                return _escalate_and_log(log_entry, db_result["error_flags"][0])

            if not db_result["author"]:
                identity_conf = 0.0

            if db_result["multiple_books"] and not (entities and entities.get("book_title")):
                titles = [b["book_title"] for b in db_result["books"]]
                response_text = (
                    f"I found multiple books under your account: {', '.join(titles)}. "
                    "Could you let me know which book you're asking about?"
                )
                log_entry.update({
                    "response": response_text,
                    "confidence": 0.6,
                    "escalated": False,
                })
                get_supabase().table("query_logs").insert(log_entry).execute()
                return ChatResponse(
                    response=response_text,
                    confidence=0.6,
                    intent=intent,
                    escalated=False,
                    author_found=True,
                    books_found=len(db_result["books"]),
                )

            if db_result["multiple_books"] and entities and entities.get("book_title"):
                title_query = entities["book_title"].lower()
                filtered = [
                    b for b in db_result["books"]
                    if title_query in b["book_title"].lower()
                ]
                if filtered:
                    db_result["books"] = filtered

        kb_text, kb_relevance = None, 0.0
        if query_type == "kb_query" or not db_result["author"]:
            kb_text, kb_relevance = knowledge_base.search_knowledge_base(req.message)

        overall_confidence = confidence_scorer.calculate_confidence(
            intent_confidence=intent_conf,
            identity_confidence=identity_conf,
            kb_relevance=kb_relevance if kb_text else 0.0,
            query_type=query_type,
        )
        log_entry["confidence"] = overall_confidence

        escalation = confidence_scorer.should_escalate(
            overall_confidence,
            intent,
            db_result.get("error_flags", []),
        )
        if escalation["escalate"]:
            return _escalate_and_log(log_entry, escalation["reason"])

        response_text = response_generator.generate_response(
            intent=intent,
            user_message=req.message,
            db_data=db_result,
            kb_context=kb_text,
        )

        log_entry.update({
            "response": response_text,
            "escalated": False,
        })
        get_supabase().table("query_logs").insert(log_entry).execute()

        return ChatResponse(
            response=response_text,
            confidence=overall_confidence,
            intent=intent,
            escalated=False,
            author_found=db_result["author"] is not None,
            books_found=len(db_result["books"]),
        )

    except Exception as exc:
        error_trace = traceback.format_exc()
        log_entry["error_info"] = error_trace[:500]
        return _escalate_and_log(log_entry, f"Unhandled exception: {str(exc)}")


@app.post("/identity/resolve")
async def resolve_identity(req: IdentityRequest):
    """
    Standalone endpoint for identity resolution demonstration.
    Shows confidence scores and signal breakdowns for a single request.
    """
    all_profiles = get_supabase().table("authors").select("*").execute().data
    result = identity_unifier.unify_identity(req.dict(), all_profiles)

    if result.get("action") == "verify_manually" and result.get("matched_author_id"):
        platform_identifier = (
            req.email
            or req.phone
            or req.instagram
            or req.name
            or "unknown"
        )
        try:
            get_supabase().table("identity_mappings").insert({
                "author_id": result["matched_author_id"],
                "platform": "api",
                "platform_identifier": platform_identifier,
                "match_confidence": result["confidence"],
                "verified": False,
            }).execute()
        except Exception:
            pass

    return result


@app.get("/admin/identity-review")
async def identity_review():
    """
    Return all unverified identity mappings for manual review.
    """
    try:
        mappings = (
            get_supabase()
            .table("identity_mappings")
            .select("*, authors(email, dashboard_name)")
            .eq("verified", False)
            .order("match_confidence")
            .execute()
        )
        return {"pending_review": mappings.data}
    except Exception as exc:
        return {"pending_review": [], "error": str(exc)}


@app.post("/admin/identity-review/{mapping_id}/approve")
async def approve_identity_mapping(mapping_id: str, body: dict = Body(default={})):
    """
    Approve a pending identity mapping by marking it verified.
    """
    try:
        res = (
            get_supabase()
            .table("identity_mappings")
            .update({"verified": True})
            .eq("id", mapping_id)
            .execute()
        )
        return {"ok": True, "updated": res.data, "note": body.get("note")}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.post("/admin/identity-review/{mapping_id}/reject")
async def reject_identity_mapping(mapping_id: str, body: dict = Body(default={})):
    """
    Reject a pending identity mapping by marking it verified.
    """
    try:
        res = (
            get_supabase()
            .table("identity_mappings")
            .update({"verified": True})
            .eq("id", mapping_id)
            .execute()
        )
        return {"ok": True, "updated": res.data, "note": body.get("note")}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.get("/health")
async def health():
    """
    Service health check including database connectivity.
    """
    try:
        get_supabase().table("authors").select("id").limit(1).execute()
        db_status = "connected"
    except Exception as exc:
        db_status = f"error: {str(exc)}"

    return {"status": "ok", "database": db_status, "version": "0.1.0"}
