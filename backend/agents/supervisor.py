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
    
    # Add nodes representing specialized agents
    workflow.add_node("memory", nodes.memory_node)
    workflow.add_node("intent", nodes.intent_node)
    workflow.add_node("identity", nodes.identity_node)
    workflow.add_node("db_dispatcher", nodes.db_retrieval_node)
    workflow.add_node("royalty_agent", nodes.royalty_agent_node)
    workflow.add_node("publishing_agent", nodes.publishing_agent_node)
    workflow.add_node("kb_retrieval", nodes.kb_retrieval_node)
    workflow.add_node("eval_node", nodes.eval_node)
    workflow.add_node("generation", nodes.generation_node)
    workflow.add_node("escalation", nodes.escalation_node)
    
    # Set entry point to memory agent to resolve histories and preferences first
    workflow.set_entry_point("memory")
    
    # Static transitions
    workflow.add_edge("memory", "intent")
    workflow.add_edge("intent", "identity")
    
    # Conditional routing after identity (DB vs KB)
    def route_retrieval(state: AgentState):
        if state.get("query_type") == "db_query":
            return "db_dispatcher"
        return "kb_retrieval"
        
    workflow.add_conditional_edges(
        "identity",
        route_retrieval,
        {
            "db_dispatcher": "db_dispatcher",
            "kb_retrieval": "kb_retrieval"
        }
    )
    
    # Conditional routing after DB dispatcher (Royalty vs Publishing)
    def route_db_agents(state: AgentState):
        return state.get("next_node", "publishing_agent")
        
    workflow.add_conditional_edges(
        "db_dispatcher",
        route_db_agents,
        {
            "royalty_agent": "royalty_agent",
            "publishing_agent": "publishing_agent"
        }
    )
    
    # Conditional routing after Royalty Agent (errors/success)
    def route_after_royalty(state: AgentState):
        if state.get("next_node") == "escalation_node":
            return "escalation"
        if state.get("next_node") == "end":
            return END
        return "kb_retrieval"
        
    workflow.add_conditional_edges(
        "royalty_agent",
        route_after_royalty,
        {
            "escalation": "escalation",
            "kb_retrieval": "kb_retrieval",
            END: END
        }
    )

    # Conditional routing after Publishing Agent (disambiguation/errors/success)
    def route_after_publishing(state: AgentState):
        if state.get("next_node") == "escalation_node":
            return "escalation"
        if state.get("next_node") == "end":
            return END
        return "kb_retrieval"
        
    workflow.add_conditional_edges(
        "publishing_agent",
        route_after_publishing,
        {
            "escalation": "escalation",
            "kb_retrieval": "kb_retrieval",
            END: END
        }
    )
    
    workflow.add_edge("kb_retrieval", "eval_node")
    
    # Conditional routing after Evaluation Agent (escalated vs generated responses)
    def route_generation(state: AgentState):
        if state.get("escalated"):
            return "escalation"
        return "generation"
        
    workflow.add_conditional_edges(
        "eval_node",
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

