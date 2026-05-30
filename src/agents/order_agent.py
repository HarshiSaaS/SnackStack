import re

from config import llm
from logger import setup_logger
from state import SnackStackState
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.types import interrupt
from agents.prompts import ORDER_AGENT_PROMPT
from tools.order_tools import order_tools_list


logger = setup_logger("snackstack.order_agent")

order_tools_by_name = {tool.name: tool for tool in order_tools_list}
order_llm = llm.bind_tools(order_tools_list)

# Patterns to detect identifiers in the user query
ORDER_ID_RE = re.compile(r"ORD-\d+", re.IGNORECASE)
TRACKING_RE = re.compile(r"SS\d+TRK", re.IGNORECASE)
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

def extract_identifier(text: str) -> str | None:
    """Try to extract an order ID, tracking ID, or email from text."""
    for pattern in (ORDER_ID_RE, TRACKING_RE, EMAIL_RE):
        match = pattern.search(text)
        if match:
            return match.group()
    return None

def order_agent_node(state: SnackStackState) -> dict:
    existing = state.get("order_messages") or []
    if not existing:
        # First call — conversation history is persisted via MemorySaver
        logger.info("Processing order query...")
        query = state["user_query"]
        print("================")
        print(query)
        print("================")
        lookup_key = extract_identifier(query)

        if lookup_key:
            logger.info("Found identifier: %s", lookup_key)
        else:
            logger.info("No identifier found — interrupting for user input")
            lookup_key = interrupt(
                "I'd be happy to help with your order! "
                "Could you please provide one of the following?\n"
                "  • Order ID    (e.g. ORD-201)\n"
                "  • Tracking ID (e.g. SS201TRK)\n"
                "  • Email       (e.g. priya@example.com)"
            )
            lookup_key = lookup_key.strip()
            logger.info("User provided: %s", lookup_key)

        all_msgs = [
            SystemMessage(content=ORDER_AGENT_PROMPT),
            HumanMessage(f"{query}\n\nLookup key: {lookup_key}"),
        ]
    else:
        # Subsequent call — tool results already in order_messages
        logger.info("Order agent re-invoked after tool results")
        all_msgs = existing

    response = order_llm.invoke(all_msgs)
    all_msgs = [*all_msgs, response]

    has_tools = bool(getattr(response, "tool_calls", None))
    logger.info("Tool calls: %s", has_tools)

    update: dict = {"order_messages": all_msgs}

    if not has_tools:
        update["order_response"] = response.content
        update["messages"] = [response]

    return update


def order_tools_node(state: SnackStackState) -> dict:
    """Execute tool calls from the last AI message in order_messages."""

    all_msgs = list(state["order_messages"])
    last_msg = all_msgs[-1]
    tool_names = [tc["name"] for tc in last_msg.tool_calls]
    logger.info("Executing tools: %s", tool_names)

    for tc in last_msg.tool_calls:
        result = order_tools_by_name[tc["name"]].invoke(tc["args"])
        all_msgs.append(
            ToolMessage(content=str(result), tool_call_id=tc["id"])
        )

    return {"order_messages": all_msgs}


def should_continue_order(state: SnackStackState) -> str:
    """Conditional edge: route to tools or synthesizer."""
    order_msgs = state.get("order_messages") or []
    if order_msgs:
        last = order_msgs[-1]
        if getattr(last, "tool_calls", None):
            return "order_tools_node"
    return "synthesizer_node"