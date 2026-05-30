from config import llm
from state import SnackStackState
from pydantic import BaseModel, Field
from logger import setup_logger
from typing import Literal
from state import AgentTask
from langgraph.types import Command, Send
from langchain_core.messages import HumanMessage, SystemMessage
from agents.prompts import ORCHESTRATOR_PROMPT

logger = setup_logger("snackstack.orchestrator")

class OrchestratorDecision(BaseModel):
    agents: list[Literal["menu_agent", "order_agent"]] = Field(
        description="List of agents to dispatch, always atleast 1",
        min_length=1,
    )
    reasoning: str = Field(description="The reasoning for the routing decision")

routing_llm = llm.with_structured_output(OrchestratorDecision)

def orchestrator_node(
    state: SnackStackState
) -> Command[Literal["menu_agent_node", "order_agent_node"]]:
    query = state["user_query"]
    logger.info("Routing query: %s", query[:60])

     # Conversation history is persisted via MemorySaver — just use it
    history = state.get("messages", [])[-6:]

    decision: OrchestratorDecision = routing_llm.invoke([
        SystemMessage(content=ORCHESTRATOR_PROMPT),
        *history,
        HumanMessage(content=query),
    ])

     # Reset per-turn buffers BEFORE sending to agents
    clean_state = {
        **state,
        "menu_messages": [],
        "order_messages": [],
        "menu_response": "",
        "order_response": "",
    }
    
    sends = [Send(f"{agent}_node", clean_state) for agent in decision.agents]

    return Command(
        update = {
            "route": decision.agents
        },
        goto = sends
    )