from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class ConversationState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    route: str
    user_name: str | None
    user_email: str | None
    selected_slot: str | None
    booking_status: str
    reference_id: str | None
    assistant_response: str