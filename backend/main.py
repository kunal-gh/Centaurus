"""
BookLeaf AI Automation — FastAPI Core Application

Endpoints:
  POST /chat               -> Main 8-stage query bot pipeline
  POST /identity/resolve   -> Standalone identity unification demo
  GET  /admin/identity-review -> Pending manual verifications
  GET  /health             -> Service and database health check

Spec Reference: Section 7.1
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

# ============================================================
# Application Initialization
# ============================================================
app = FastAPI(
    title="BookLeaf AI Automation",
    description="Workflow-aware customer query bot with identity unification",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the minimal demo UI (no build step)
# Visit: http://localhost:8000/app/
app.mount("/app", StaticFiles(directory="web", html=True), name="web")


@app.get("/")
async def root():
    return RedirectResponse(url="/app/")


# ============================================================
# Startup: Pre-build KB embeddings cache
# ============================================================
@app.on_event("startup")
async def startup_event():
    """
    Pre-builds the knowledge base embedding cache on application startup.
    Prevents first-request latency from embedding 8 KB chunks.
    """
    knowledge_base.build_kb_cache()


# ============================================================
# Helper: Escalation Logger
# ============================================================
def _escalate_and_log(log_entry: dict, reason: str) -> ChatResponse:
    """
    Standardized escalation handler used by all failure paths.

    - Constructs the human-handoff message
    - Updates log_entry with escalation metadata
    - Inserts into query_logs (silently ignores DB failure to avoid cascading errors)
    - Returns ChatResponse with escalated=True

    Args:
        log_entry: Mutable dict being built throughout the pipeline
        reason: Human-readable explanation for escalation

    Returns:
        ChatResponse with confidence=0.0 and escalated=True
    """
    message = (
        "I want to make sure you get the most accurate help. "
        "I've escalated your query to a BookLeaf support specialist "
        "who will respond within 24 business hours. "
        f"[Escalation reason: {reason}]"
    )

    log_entry.update({
        "escalated": True,
        "escalation_reason": reason,
        "response": message,
        "confidence": 0.0,
    })

    # Attempt logging; fail silently if DB is down to avoid cascading errors
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


# ============================================================
# Endpoint 1: POST /chat (Mandatory Task — 8-Stage Pipeline)
# ============================================================
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Main query processing pipeline.

    Stage 1: Intent Classification (OpenAI JSON mode)
    Stage 2: Identity Resolution (fuzzy + LLM via identity_unifier)
    Stage 3: Data Retrieval (Supabase author + books lookup)
    Stage 4: Knowledge Base Search (RAG cosine similarity)
    Stage 5: Confidence Scoring (weighted composite formula)
    Stage 6: Escalation Check (80% circuit breaker)
    Stage 7: Response Generation (OpenAI natural language)
    Stage 8: Logging (Supabase query_logs insert)
    """

    # Initialize log entry — populated throughout pipeline
    log_entry = {
        "channel": req.channel,
        "raw_query": req.message,
        "escalated": False,
    }

    try:
        # --------------------------------------------------------
        # Stage 1: Intent Classification
        # --------------------------------------------------------
        intent_data = intent_classifier.classify_query(req.message)
        intent = intent_data.get("intent", "unknown")
        intent_conf = intent_data.get("confidence", 0.5)
        entities = intent_data.get("entities", {})
        query_type = intent_data.get("query_type", "kb_query")

        log_entry["intent"] = intent

        # Resolve email: prefer explicit request field, fall back to LLM-extracted entity
        resolved_email = req.user_email or (entities.get("email") if entities else None)
        resolved_phone = req.user_phone

        # Classifiers only see `req.message`; API/channel may still supply email/phone fields.
        # If we would wrongly skip Supabase for record-level intents, force a DB lookup when identifiers exist.
        _record_intents = {
            "publishing_timeline",
            "royalty_status",
            "dashboard_access",
            "addon_status",
            "author_copy",
            "book_sales",
        }
        if (resolved_email or resolved_phone) and intent in _record_intents and query_type == "kb_query":
            query_type = "db_query"

        # --------------------------------------------------------
        # Stage 2: Identity Resolution
        # --------------------------------------------------------
        identity_conf = 0.5  # Default when no identity signals present
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

            # Save borderline case to identity_mappings table for manual review
            if identity_result.get("action") == "verify_manually" and author_id:
                platform_identifier = (
                    resolved_email or 
                    resolved_phone or 
                    req.user_instagram or 
                    req.user_name or 
                    "unknown"
                )
                try:
                    get_supabase().table("identity_mappings").insert({
                        "author_id": author_id,
                        "platform": req.channel,
                        "platform_identifier": platform_identifier,
                        "match_confidence": identity_conf,
                        "verified": False
                    }).execute()
                except Exception:
                    pass  # Fail-safe: ignore DB logging error to prevent pipeline failure

        # --------------------------------------------------------
        # Stage 3: Data Retrieval
        # --------------------------------------------------------
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

            # Error: DB unreachable or query failure
            if db_result["error_flags"]:
                return _escalate_and_log(log_entry, db_result["error_flags"][0])

            # No author match found — lower identity confidence
            if not db_result["author"]:
                identity_conf = 0.0

            # Multiple books found and no specific title mentioned — ask for clarification
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

            # Multiple books AND specific title mentioned — filter to matching book
            if db_result["multiple_books"] and entities and entities.get("book_title"):
                title_query = entities["book_title"].lower()
                filtered = [
                    b for b in db_result["books"]
                    if title_query in b["book_title"].lower()
                ]
                if filtered:
                    db_result["books"] = filtered

        # --------------------------------------------------------
        # Stage 4: Knowledge Base Search
        # --------------------------------------------------------
        kb_text, kb_relevance = None, 0.0
        if query_type == "kb_query" or not db_result["author"]:
            kb_text, kb_relevance = knowledge_base.search_knowledge_base(req.message)

        # --------------------------------------------------------
        # Stage 5: Confidence Scoring
        # --------------------------------------------------------
        overall_confidence = confidence_scorer.calculate_confidence(
            intent_confidence=intent_conf,
            identity_confidence=identity_conf,
            kb_relevance=kb_relevance if kb_text else 0.0,
            query_type=query_type,
        )
        log_entry["confidence"] = overall_confidence

        # --------------------------------------------------------
        # Stage 6: Escalation Check (80% Circuit Breaker)
        # --------------------------------------------------------
        escalation = confidence_scorer.should_escalate(
            overall_confidence,
            intent,
            db_result.get("error_flags", []),
        )
        if escalation["escalate"]:
            return _escalate_and_log(log_entry, escalation["reason"])

        # --------------------------------------------------------
        # Stage 7: Response Generation
        # --------------------------------------------------------
        response_text = response_generator.generate_response(
            intent=intent,
            user_message=req.message,
            db_data=db_result,
            kb_context=kb_text,
        )

        # --------------------------------------------------------
        # Stage 8: Logging — always runs on successful pipeline
        # --------------------------------------------------------
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

    except Exception as e:
        # Catch-all: any unhandled exception triggers escalation
        # Traceback is captured but not exposed to user
        error_trace = traceback.format_exc()
        log_entry["error_info"] = error_trace[:500]  # Truncate for DB storage
        return _escalate_and_log(log_entry, f"Unhandled exception: {str(e)}")


# ============================================================
# Endpoint 2: POST /identity/resolve (Intermediate Task Demo)
# ============================================================
@app.post("/identity/resolve")
async def resolve_identity(req: IdentityRequest):
    """
    Standalone endpoint for Identity Unification demonstration.
    Shows fuzzy matching confidence scores and signal breakdowns.

    Example (Sara Johnson case from assignment):
    {
      "email": "sara.johnson@xyz.com",
      "phone": "+91 9876543210",
      "name": "Sara J.",
      "instagram": "@sarapoetry23"
    }
    Expected: action=auto_link, confidence=1.0, all 4 signals matched
    """
    all_profiles = get_supabase().table("authors").select("*").execute().data
    result = identity_unifier.unify_identity(req.dict(), all_profiles)

    # Save borderline matches for review
    if result.get("action") == "verify_manually" and result.get("matched_author_id"):
        platform_identifier = (
            req.email or 
            req.phone or 
            req.instagram or 
            req.name or 
            "unknown"
        )
        try:
            get_supabase().table("identity_mappings").insert({
                "author_id": result["matched_author_id"],
                "platform": "api",
                "platform_identifier": platform_identifier,
                "match_confidence": result["confidence"],
                "verified": False
            }).execute()
        except Exception:
            pass  # fail-safe

    return result


# ============================================================
# Endpoint 3: GET /admin/identity-review
# ============================================================
@app.get("/admin/identity-review")
async def identity_review():
    """
    Returns all unverified identity mappings for manual human review.
    Shows pending matches where action was 'verify_manually'.
    Ordered by match_confidence (lowest first — most urgent review needed).
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
    except Exception as e:
        return {"pending_review": [], "error": str(e)}


@app.post("/admin/identity-review/{mapping_id}/approve")
async def approve_identity_mapping(mapping_id: str, body: dict = Body(default={})):
    """
    Approves a pending identity mapping by marking it verified.
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
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/admin/identity-review/{mapping_id}/reject")
async def reject_identity_mapping(mapping_id: str, body: dict = Body(default={})):
    """
    Rejects a pending identity mapping by marking it verified.
    (Schema is minimal; 'verified=true' removes it from the review queue.)
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
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ============================================================
# Endpoint 4: GET /health
# ============================================================
@app.get("/health")
async def health():
    """
    Service health check including database connectivity.
    Returns status, database connection state, and application version.
    """
    try:
        get_supabase().table("authors").select("id").limit(1).execute()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {"status": "ok", "database": db_status, "version": "1.0.0"}
