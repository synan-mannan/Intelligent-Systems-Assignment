import asyncio

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage

from app.graph.graph import conversation_graph
from app.models.schemas import AppointmentSlot, ChatRequest, ChatResponse
from app.tools.booking import available_slots

router = APIRouter(prefix="/api")


@router.get("/slots", response_model=list[AppointmentSlot])
async def get_slots() -> list[dict[str, str]]:
    return await asyncio.to_thread(available_slots)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    config = {"configurable": {"thread_id": request.thread_id}}
    try:
        state = await conversation_graph.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
        )
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="The assistant could not complete the request.") from error

    return ChatResponse(
        thread_id=request.thread_id,
        response=state["assistant_response"],
        booking_status=state.get("booking_status", "not_started"),
        user_name=state.get("user_name"),
        user_email=state.get("user_email"),
        selected_slot=state.get("selected_slot"),
        reference_id=state.get("reference_id"),
    )