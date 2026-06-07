"""
Centaurus - FastAPI control plane.

Endpoints:
  POST /chat                  -> Main answer pipeline
  POST /identity/resolve      -> Standalone identity resolution demo
  GET  /admin/identity-review -> Pending reviewer decisions
  GET  /health                -> Service and database health check
"""
import traceback
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from backend.models import ChatRequest, ChatResponse, IdentityRequest, ResolveRequest
from backend.database import get_supabase
from backend.telemetry import tracing
from backend.agents.supervisor import centaurus_app


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
    Instrumented 8-stage answer pipeline (Wave 2: full Langfuse tracing).

    1. Intent classification       → span: intent_classification
    2. Identity resolution         → span: identity_resolution
    3. Structured record retrieval → span: db_retrieval
    4. Knowledge retrieval (RAG)   → span: kb_retrieval
    5. Confidence scoring          → span: confidence_scoring
    6. Escalation check            (inline, no separate span)
    7. Response generation         → span: response_generation
    8. Audit logging + trace close
    """
    t_total = tracing.timer()

    log_entry = {
        "channel": req.channel,
        "raw_query": req.message,
        "escalated": False,
    }

    # Open a top-level Langfuse trace for this request
    trace = tracing.start_trace(
        name="chat",
        input={"message": req.message, "channel": req.channel},
        metadata={"user_email": req.user_email, "user_name": req.user_name},
    )
    trace_id = tracing.get_trace_id(trace)
    if trace_id:
        log_entry["trace_id"] = trace_id

    try:
        # Initialize the LangGraph state
        initial_state = {
            "channel": req.channel,
            "raw_query": req.message,
            "user_email": req.user_email,
            "user_phone": req.user_phone,
            "user_name": req.user_name,
            "user_instagram": req.user_instagram,
            "trace_id": trace_id,
            "intent": "unknown",
            "intent_confidence": 0.5,
            "entities": {},
            "query_type": "kb_query",
            "author_id": None,
            "identity_confidence": 0.5,
            "identity_action": None,
            "db_result": {"author": None, "books": [], "error_flags": [], "multiple_books": False},
            "kb_text": None,
            "graph_text": None,
            "kb_relevance": 0.0,
            "kb_sources": [],
            "overall_confidence": 0.5,
            "escalated": False,
            "escalation_reason": None,
            "response": "",
            "next_node": ""
        }
        
        # Execute the LangGraph State Machine
        # A thread_id is required if checkpointing is enabled
        config = {"configurable": {"thread_id": trace_id or "default_thread"}}
        final_state = centaurus_app.invoke(initial_state, config=config)
        
        # Extract outputs
        response_text = final_state.get("response", "")
        overall_confidence = final_state.get("overall_confidence", 0.0)
        intent = final_state.get("intent", "unknown")
        escalated = final_state.get("escalated", False)
        author_found = bool(final_state.get("author_id"))
        books_found = len(final_state.get("db_result", {}).get("books", []))
        kb_sources = final_state.get("kb_sources", [])

        # Audit Logging
        log_entry.update({
            "intent": intent,
            "author_id": final_state.get("author_id"),
            "confidence": overall_confidence,
            "response": response_text,
            "escalated": escalated,
            "escalation_reason": final_state.get("escalation_reason")
        })
        get_supabase().table("query_logs").insert(log_entry).execute()

        # Close trace
        tracing.end_trace(
            trace,
            output={
                "response": response_text,
                "confidence": overall_confidence,
                "intent": intent,
                "escalated": escalated,
                "sources": len(kb_sources),
            },
            metadata={"total_latency_ms": tracing.elapsed_ms(t_total)},
        )

        return ChatResponse(
            response=response_text,
            confidence=overall_confidence,
            intent=intent,
            escalated=escalated,
            reason=final_state.get("escalation_reason"),
            author_found=author_found,
            books_found=books_found,
            sources=kb_sources if kb_sources else None,
        )

    except Exception as exc:
        tracing.end_trace(trace, output={"error": str(exc)}, level="ERROR")
        raise HTTPException(status_code=500, detail=str(exc))


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
    Reject a pending identity mapping by deleting it from the queue.
    A rejected mapping is removed entirely — it should not influence future scoring.
    The optional 'note' is returned for audit trail purposes but not persisted here.
    """
    try:
        res = (
            get_supabase()
            .table("identity_mappings")
            .delete()
            .eq("id", mapping_id)
            .execute()
        )
        return {"ok": True, "deleted": res.data, "note": body.get("note")}
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

# ── Wave 5: RLHF & Human-in-the-Loop Admin Endpoints ───────────────────────────

@app.get("/admin/escalations")
def get_escalations():
    """
    Returns recent queries that were escalated to a human.
    """
    try:
        data = get_supabase().table("query_logs").select("*").eq("escalated", True).order("created_at", desc=True).limit(50).execute()
        return {"escalations": data.data}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/admin/resolve")
def resolve_escalation(req: ResolveRequest):
    """
    Reviewer submits the correct answer. We save it to `reviewer_decisions`
    so we can fine-tune the model with DPO later.
    """
    try:
        # Get the original query log to fetch the model's failed response
        log_data = get_supabase().table("query_logs").select("response").eq("id", req.query_log_id).execute()
        if not log_data.data:
            raise HTTPException(status_code=404, detail="Query log not found")
            
        original_response = log_data.data[0].get("response", "")
        
        # Insert into reviewer decisions
        get_supabase().table("reviewer_decisions").insert({
            "query_log_id": req.query_log_id,
            "original_response": original_response,
            "approved_response": req.approved_response,
            "rationale": req.rationale,
            "reviewed_by": req.reviewed_by
        }).execute()
        
        # Mark as resolved in query_logs
        get_supabase().table("query_logs").update({
            "escalated": False,
            "escalation_reason": "Resolved by Human"
        }).eq("id", req.query_log_id).execute()
        
        return {"status": "success", "message": "Decision recorded for DPO"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
