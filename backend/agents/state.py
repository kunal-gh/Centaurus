"""
LangGraph State Definition for Centaurus.
Defines the global state object passed between specialist agents during the chat pipeline.
"""
from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    # Core request
    channel: str
    raw_query: str
    user_email: Optional[str]
    user_phone: Optional[str]
    user_name: Optional[str]
    user_instagram: Optional[str]
    
    # Trace tracking
    trace_id: Optional[str]

    # Intent & Identity Context
    intent: str
    intent_confidence: float
    entities: Dict[str, Any]
    query_type: str  # kb_query or db_query
    
    author_id: Optional[str]
    identity_confidence: float
    identity_action: Optional[str]

    # Retrieval Context
    db_result: Dict[str, Any]
    kb_text: Optional[str]
    graph_text: Optional[str]
    kb_relevance: float
    kb_sources: List[Dict[str, Any]]
    
    # Final Outputs
    overall_confidence: float
    escalated: bool
    escalation_reason: Optional[str]
    response: str
    
    # ── Waves 2 & 3: Memory and Evaluation Dashboard State Extensions ───────────
    history_summary: Optional[str]        # Episodic Memory summary of previous sessions
    user_preferences: Dict[str, Any]      # Preference Memory (style, tone, verified_user, etc.)
    quality_eval_scores: Dict[str, float]  # Live quality metrics (faithfulness, relevancy, graph_coverage)
    visited_nodes: List[str]              # List of nodes visited for routing audit logs
    
    # Routing
    next_node: str

