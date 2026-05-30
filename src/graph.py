from state import SnackStackState
from langgraph.graph import StateGraph
from logger import setup_logger
from agents.orchestrator import orchestrator_node
from agents.menu_agent import menu_agent_node, menu_tools_node
from agents.order_agent import order_agent_node, order_tools_node
from agents.synthesizer import synthesizer_node
from langgraph.graph import START, END
from langgraph.checkpoint.memory import MemorySaver
from agents.menu_agent import menu_agent_node, menu_tools_node, should_continue_menu
from agents.order_agent import order_agent_node, order_tools_node, should_continue_order

logger = setup_logger("snackstack.graph")

def build_graph():
    """Construct, compile, and return the SnackStack graph."""
    
    builder = StateGraph(SnackStackState)

    # ── Add nodes ───────────────────────────────────────────────────────────────
    builder.add_node("orchestrator", orchestrator_node)
    builder.add_node("menu_agent_node", menu_agent_node)
    builder.add_node("menu_tools_node", menu_tools_node)
    builder.add_node("order_agent_node", order_agent_node)
    builder.add_node("order_tools_node", order_tools_node)
    builder.add_node("synthesizer_node", synthesizer_node)

    # ── Add edges ────────────────────────────────────────────────────────────────
    builder.add_edge(START, "orchestrator")

    # orchestrator → agent(s) routing handled via Command + Send()
    # builder.add_edge("orchestrator", "menu_agent_node")

    builder.add_conditional_edges(
        "menu_agent_node",
        should_continue_menu,
        {
            "menu_tools_node": "menu_tools_node",
            "synthesizer_node": "synthesizer_node",
        },
    )
    builder.add_edge("menu_tools_node", "menu_agent_node")

    # orchestrator → agent(s) routing handled via Command + Send()
    # builder.add_edge("orchestrator", "order_agent_node")

    builder.add_conditional_edges(
        "order_agent_node",
        should_continue_order,
        {
            "order_tools_node": "order_tools_node",
            "synthesizer_node": "synthesizer_node",
        },
    )
    builder.add_edge("order_tools_node", "order_agent_node")

    builder.add_edge("synthesizer_node", END)

    # ── Compile with checkpointer ────────────────────────
    # MemorySaver persists graph state so that interrupt()-based
    # HITL can pause and resume, and conversation history carries
    # forward between queries.
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)

    logger.info("Graph compiled  (with MemorySaver for conversation persistence)")
    return graph