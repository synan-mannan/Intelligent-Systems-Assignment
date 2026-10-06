from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.graph.nodes import booking_node, faq_node, router_node
from app.graph.state import ConversationState

builder = StateGraph(ConversationState)
builder.add_node("router", router_node)
builder.add_node("faq", faq_node)
builder.add_node("booking", booking_node)
builder.add_edge(START, "router")
builder.add_conditional_edges(
    "router",
    lambda state: state["route"],
    {"faq": "faq", "booking": "booking"},
)
builder.add_edge("faq", END)
builder.add_edge("booking", END)

conversation_graph = builder.compile(checkpointer=MemorySaver())