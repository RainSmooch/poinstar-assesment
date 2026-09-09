from langgraph.graph import StateGraph, START, END
from src.state import AcademicAgentState
from src.nodes.guard import scope_guard_node, reject_node
from src.nodes.thinking import thinking_node
from src.nodes.tools_node import retrieve_tools_node
from src.nodes.generator import generate_response_node
from src.memory import get_checkpointer

def route_by_scope(state: AcademicAgentState) -> str:
    if state.get("is_in_scope", True):
        return "thinking_node"
    return "reject_node"

def build_graph(checkpointer=None):
    workflow = StateGraph(AcademicAgentState)

    # Tambahkan nodes
    workflow.add_node("guard_node", scope_guard_node)
    workflow.add_node("reject_node", reject_node)
    workflow.add_node("thinking_node", thinking_node)
    workflow.add_node("retrieve_tools_node", retrieve_tools_node)
    workflow.add_node("generator_node", generate_response_node)

    # Tambahkan edges
    workflow.add_edge(START, "guard_node")
    
    workflow.add_conditional_edges(
        "guard_node",
        route_by_scope,
        {
            "thinking_node": "thinking_node",
            "reject_node": "reject_node"
        }
    )

    workflow.add_edge("reject_node", END)
    workflow.add_edge("thinking_node", "retrieve_tools_node")
    workflow.add_edge("retrieve_tools_node", "generator_node")
    workflow.add_edge("generator_node", END)

    if checkpointer is None:
        checkpointer = get_checkpointer()

    return workflow.compile(checkpointer=checkpointer)

# Instance default
agent_graph = None

def get_agent_graph():
    global agent_graph
    if agent_graph is None:
        agent_graph = build_graph()
    return agent_graph
