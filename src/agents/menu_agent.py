from tools import menu_tools
from config import llm
from logger import setup_logger
from state import SnackStackState
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from agents.prompts import MENU_AGENT_PROMPT
from tools.menu_tools import menu_tools_list

logger = setup_logger("snackstack.menu_agent")

menu_tools_by_name = {tool.name: tool for tool in menu_tools_list}

menu_llm = llm.bind_tools(menu_tools_list)


def menu_agent_node(state: SnackStackState) -> dict:
    existing = state.get("menu_messages") or []

    if not existing:
        # First call — conversation history is persisted via MemorySaver
        logger.info("Processing menu query...")
        history = state.get("messages", [])[-6:]

        all_msgs = [
            SystemMessage(content=MENU_AGENT_PROMPT),
            *history,
            HumanMessage(content=state["user_query"]),
        ]
    else:
        # Subsequent call — tool results already in menu_messages
        logger.info("Menu agent re-invoked after tool results")
        all_msgs = existing

    response = menu_llm.invoke(all_msgs)
    all_msgs = [*all_msgs, response]

    has_tools = bool(getattr(response, "tool_calls", None))
    logger.info("Tool calls: %s", has_tools)

    update: dict = {"menu_messages": all_msgs}

    if not has_tools:
        update["menu_response"] = response.content
        update["messages"] = [response]

    return update

def menu_tools_node(state: SnackStackState) -> dict:
    all_msgs = list(state["menu_messages"])
    last_msg = all_msgs[-1]
    
    for tool_call in last_msg.tool_calls:
        name, args = tool_call["name"], tool_call["args"]
        result = menu_tools_by_name[name].invoke(args) if name in menu_tools_by_name else "Unknown tool: " + name
        print(result)
        all_msgs.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
    
    return {"menu_messages": all_msgs}

def should_continue_menu(state: SnackStackState) -> str:
    """Conditional edge: route to tools or synthesizer."""
    menu_msgs = state.get("menu_messages") or []
    if menu_msgs:
        last = menu_msgs[-1]
        if getattr(last, "tool_calls", None):
            return "menu_tools_node"
    return "synthesizer_node"
