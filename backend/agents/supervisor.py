"""
Centaurus LangGraph Supervisor.
Compiles the state nodes into an executable StateGraph and manages routing.
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from backend.agents.state import AgentState
from backend.agents import nodes

def build_graph() -> StateGraph:
    """
    Builds the Centaurus Multi-Agent workflow graph.
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("intent", nodes.intent_node)
    workflow.add_node("identity", nodes.identity_node)
    workflow.add_node("db_retrieval", nodes.db_retrieval_node)
    workflow.add_node("kb_retrieval", nodes.kb_retrieval_node)
    workflow.add_node("confidence", nodes.confidence_node)
    workflow.add_node("generation", nodes.generation_node)
    workflow.add_node("escalation", nodes.escalation_node)
    
    # Add edges
    workflow.set_entry_point("intent")
    workflow.add_edge("intent", "identity")
    
    # Conditional routing after identity
    def route_retrieval(state: AgentState):
        if state.get("query_type") == "db_query" and (state.get("user_email") or state.get("user_phone") or state.get("entities", {}).get("email")):
            return "db_retrieval"
        return "kb_retrieval"
        
    workflow.add_conditional_edges(
        "identity",
        route_retrieval,
        {
            "db_retrieval": "db_retrieval",
            "kb_retrieval": "kb_retrieval"
        }
    )
    
    # Conditional routing after DB retrieval (disambiguation/error vs success)
    def route_after_db(state: AgentState):
        if state.get("next_node") == "escalation_node":
            return "escalation"
        if state.get("next_node") == "end":
            return END
        return "kb_retrieval"
        
    workflow.add_conditional_edges(
        "db_retrieval",
        route_after_db,
        {
            "escalation": "escalation",
            "kb_retrieval": "kb_retrieval",
            END: END
        }
    )
    
    workflow.add_edge("kb_retrieval", "confidence")
    
    # Conditional routing after confidence
    def route_generation(state: AgentState):
        if state.get("escalated"):
            return "escalation"
        return "generation"
        
    workflow.add_conditional_edges(
        "confidence",
        route_generation,
        {
            "escalation": "escalation",
            "generation": "generation"
        }
    )
    
    workflow.add_edge("generation", END)
    workflow.add_edge("escalation", END)
    
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
    
# Singleton compiled graph instance
centaurus_app = build_graph()
