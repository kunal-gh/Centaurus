"""
Specialist Nodes for the Centaurus LangGraph.
Each function represents a discrete pipeline stage that takes AgentState,
updates it based on business logic, and returns the modified fields.
"""
from backend.agents.state import AgentState
from backend.services import (
    intent_classifier,
    identity_unifier,
    data_retriever,
    knowledge_base,
    graph_retriever,
    confidence_scorer,
    response_generator
)
from backend.database import get_supabase
from backend.telemetry import tracing

def intent_node(state: AgentState) -> dict:
    t0 = tracing.timer()
    span = tracing.start_span(None, "intent_node") # Tracing can be injected manually or via callback
    
    intent_data = intent_classifier.classify_query(state["raw_query"])
    intent = intent_data.get("intent", "unknown")
    
    # Check if this is a db_query
    query_type = intent_data.get("query_type", "kb_query")
    resolved_email = state.get("user_email") or (intent_data.get("entities", {}).get("email"))
    resolved_phone = state.get("user_phone")
    
    record_intents = {
        "publishing_timeline", "royalty_status", "dashboard_access", 
        "addon_status", "author_copy", "book_sales",
    }
    if (resolved_email or resolved_phone) and intent in record_intents and query_type == "kb_query":
        query_type = "db_query"
        
    tracing.end_span(span)
    
    return {
        "intent": intent,
        "intent_confidence": intent_data.get("confidence", 0.5),
        "entities": intent_data.get("entities", {}),
        "query_type": query_type,
        "next_node": "identity_node"
    }


def identity_node(state: AgentState) -> dict:
    resolved_email = state.get("user_email") or state["entities"].get("email")
    resolved_phone = state.get("user_phone")
    
    if not any([resolved_email, resolved_phone, state.get("user_name"), state.get("user_instagram")]):
        return {"identity_confidence": 0.5, "author_id": None, "next_node": "retrieval_router"}
        
    all_profiles = get_supabase().table("authors").select("*").execute().data
    identity_result = identity_unifier.unify_identity(
        {
            "email": resolved_email,
            "phone": resolved_phone,
            "name": state.get("user_name"),
            "instagram": state.get("user_instagram"),
        },
        all_profiles,
    )
    
    author_id = identity_result.get("matched_author_id")
    action = identity_result.get("action")
    
    if action == "verify_manually" and author_id:
        platform_identifier = resolved_email or resolved_phone or state.get("user_instagram") or state.get("user_name") or "unknown"
        try:
            get_supabase().table("identity_mappings").insert({
                "author_id": author_id,
                "platform": state["channel"],
                "platform_identifier": platform_identifier,
                "match_confidence": identity_result["confidence"],
                "verified": False,
            }).execute()
        except Exception:
            pass

    return {
        "author_id": author_id,
        "identity_confidence": identity_result["confidence"],
        "identity_action": action,
        "next_node": "retrieval_router"
    }


def db_retrieval_node(state: AgentState) -> dict:
    resolved_email = state.get("user_email") or state["entities"].get("email")
    resolved_phone = state.get("user_phone")
    
    db_result = data_retriever.fetch_author_and_books(
        email=resolved_email,
        phone=resolved_phone,
    )
    
    # Handle error flags
    if db_result["error_flags"]:
        return {
            "db_result": db_result,
            "escalated": True,
            "escalation_reason": db_result["error_flags"][0],
            "next_node": "escalation_node"
        }
        
    # Handle disambiguation
    if db_result["multiple_books"] and not state["entities"].get("book_title"):
        titles = [b["book_title"] for b in db_result["books"]]
        response_text = f"I found multiple books under your account: {', '.join(titles)}. Could you let me know which book you're asking about?"
        return {
            "db_result": db_result,
            "response": response_text,
            "overall_confidence": 0.6,
            "next_node": "end"
        }
        
    if db_result["multiple_books"] and state["entities"].get("book_title"):
        title_query = state["entities"]["book_title"].lower()
        filtered = [b for b in db_result["books"] if title_query in b["book_title"].lower()]
        if filtered:
            db_result["books"] = filtered

    identity_confidence = state["identity_confidence"]
    if not db_result["author"]:
        identity_confidence = 0.0

    return {
        "db_result": db_result,
        "identity_confidence": identity_confidence,
        "next_node": "kb_retrieval_node"
    }


def kb_retrieval_node(state: AgentState) -> dict:
    # 1. Graph Context
    graph_text = ""
    if state.get("author_id"):
        graph_text = graph_retriever.extract_graph_context_for_query(state["intent"], state["author_id"])
        
    # 2. Vector Context
    hybrid_results = knowledge_base.search_knowledge_base_hybrid(state["raw_query"], top_k=3)
    kb_text = None
    kb_relevance = 0.0
    kb_sources = []
    
    if hybrid_results:
        best_match = hybrid_results[0]
        kb_text = best_match["text"]
        kb_relevance = best_match["score"]
        kb_sources = [{
            "chunk_id": r["metadata"].get("chunk_id"),
            "section": r["metadata"].get("section"),
            "source": r["metadata"].get("source"),
            "score": r["score"]
        } for r in hybrid_results]
        
    return {
        "graph_text": graph_text,
        "kb_text": kb_text,
        "kb_relevance": kb_relevance,
        "kb_sources": kb_sources,
        "next_node": "confidence_node"
    }


def confidence_node(state: AgentState) -> dict:
    overall_confidence = confidence_scorer.calculate_confidence(
        intent_confidence=state["intent_confidence"],
        identity_confidence=state["identity_confidence"],
        kb_relevance=state["kb_relevance"] if state.get("kb_text") else 0.0,
        query_type=state["query_type"],
    )
    
    escalation = confidence_scorer.should_escalate(
        overall_confidence,
        state["intent"],
        state.get("db_result", {}).get("error_flags", []),
    )
    
    if escalation["escalate"]:
        return {
            "overall_confidence": overall_confidence,
            "escalated": True,
            "escalation_reason": escalation["reason"],
            "next_node": "escalation_node"
        }
        
    return {
        "overall_confidence": overall_confidence,
        "escalated": False,
        "next_node": "generation_node"
    }


def generation_node(state: AgentState) -> dict:
    final_context = []
    if state.get("graph_text"):
        final_context.append(state["graph_text"])
    if state.get("kb_text"):
        final_context.append(f"[Document Knowledge Base]\n{state['kb_text']}")
        
    merged_kb_text = "\n\n".join(final_context) if final_context else None

    response_text = response_generator.generate_response(
        intent=state["intent"],
        user_message=state["raw_query"],
        db_data=state.get("db_result", {"author": None, "books": []}),
        kb_context=merged_kb_text,
    )
    
    return {
        "response": response_text,
        "next_node": "end"
    }


def escalation_node(state: AgentState) -> dict:
    reason = state.get("escalation_reason", "Low confidence")
    message = (
        "I want to make sure you get the most accurate help. "
        "I've escalated your query to a Centaurus reviewer "
        "who will respond within 24 business hours. "
        f"[Escalation reason: {reason}]"
    )
    
    return {
        "response": message,
        "overall_confidence": 0.0,
        "next_node": "end"
    }
