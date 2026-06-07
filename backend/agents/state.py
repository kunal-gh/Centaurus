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
    
    # Routing
    next_node: str
