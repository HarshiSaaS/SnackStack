import uuid

from graph import build_graph

graph = build_graph()

result = graph.invoke(
    {
        "user_query": "What vegan dishes are there?"
    },
    {"configurable": {"thread_id": str(uuid.uuid4())}}
)

print(result.get("final_answer", "Sorry, I could not process your request."))
