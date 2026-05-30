import sys
from agents.menu_agent import menu_agent_node
from agents.order_agent import order_agent_node
from agents.synthesizer import synthesizer_node
from agents.orchestrator import orchestrator_node
from langchain_core.messages import SystemMessage, HumanMessage
from agents.prompts import ORCHESTRATOR_PROMPT, MENU_AGENT_PROMPT, ORDER_AGENT_PROMPT, SYNTHESIZER_PROMPT


orchestrator_test = {
    "user_query": "What is the menu?",
    "messages": [
        SystemMessage(content=ORCHESTRATOR_PROMPT),
        HumanMessage(content="What is the menu?"),
    ],
}

menu_agent_test = {
    "user_query": "What is the menu?",
    "messages": [
        SystemMessage(content=MENU_AGENT_PROMPT),
        HumanMessage(content="What is the menu?"),
    ],
}

order_agent_test = {
    "user_query": "ORD-201",
    "messages": [
        SystemMessage(content=ORDER_AGENT_PROMPT),
        HumanMessage(content="ORD-201"),
    ],
}

synthesizer_test = {
    "user_query": "What is the menu?",
    "messages": [
        SystemMessage(content=SYNTHESIZER_PROMPT),
        HumanMessage(content="What is the menu?"),
    ],
}

print(orchestrator_node(orchestrator_test))
print(menu_agent_node(menu_agent_test))
print(order_agent_node(order_agent_test))
print(synthesizer_node(synthesizer_test))