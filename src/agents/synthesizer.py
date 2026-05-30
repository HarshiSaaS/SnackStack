from logger import setup_logger
from state import SnackStackState
from langchain_core.messages import HumanMessage, SystemMessage
from agents.prompts import SYNTHESIZER_PROMPT
from config import llm

logger = setup_logger("snackstack.synthesizer")


def synthesizer_node(state: SnackStackState) -> dict:
    """Combine agent outputs into a final, friendly answer."""
    logger.info("Combining agent responses...")

    menu_resp = state.get("menu_response", "")
    order_resp = state.get("order_response", "")

    combined = ""
    if menu_resp:
        combined += f"[Menu Agent]\n{menu_resp}\n\n"
    if order_resp:
        combined += f"[Order Agent]\n{order_resp}\n"

    if not combined.strip():
        combined = "I could not find relevant information. Please try rephrasing your query."

    final = llm.invoke(
        [
            SystemMessage(content=SYNTHESIZER_PROMPT),
            HumanMessage(
                content=f"Customer query: {state['user_query']}\n\nAgent outputs:\n{combined}"
            ),
        ]
    )
    logger.info("Final answer ready (%d chars)", len(final.content))

    return {
        "final_answer": final.content,
        "messages": [final],
    }