from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    thread_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    thread_id: str
    response: str
    booking_status: str
    user_name: str | None = None
    user_email: str | None = None
    selected_slot: str | None = None
    reference_id: str | None = None


class AppointmentSlot(BaseModel):
    id: str
    label: str