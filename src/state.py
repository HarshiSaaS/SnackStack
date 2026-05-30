import operator

from typing import TypedDict, List, Annotated, Literal
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

class AgentTask(BaseModel):
    agent: Literal["menu_agent", "order_agent"]
    task_description: str = Field(
        description="What the agent should do"
    )

class SnackStackState(TypedDict):
    # Conversation
    messages: Annotated[List[AnyMessage], add_messages]
    user_query: str

    route: Literal["menu", "order"]

    # Agent-local message buffers (isolated via add_messages reducer)
    menu_messages: Annotated[List[AnyMessage], add_messages]
    order_messages: Annotated[List[AnyMessage], add_messages]

    # Agent outputs
    menu_response: str
    order_response: str
    final_answer: str
