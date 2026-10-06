import os
import re

from langchain_core.messages import AIMessage
from langchain_groq import ChatGroq

from app.rag.retriever import retrieve_handbook_context
from app.tools.booking import (
    available_slots,
    confirmation_reference,
    extract_contact,
    selected_slot,
)

QUESTION_START = re.compile(
    r"\b(what|when|where|why|how|who|which|does|do|is|are|can|could|tell me|explain)\b",
    re.IGNORECASE,
)
BOOKING_ACTION = re.compile(r"\b(book|schedule|reserve|set up)\b", re.IGNORECASE)


def router_node(state: dict) -> dict:
    message = str(state["messages"][-1].content)
    name, email = extract_contact(message)
    update: dict = {}
    if name:
        update["user_name"] = name
    if email:
        update["user_email"] = email

    is_question = "?" in message or bool(QUESTION_START.search(message))
    is_booking_request = bool(BOOKING_ACTION.search(message)) and not is_question
    status = state.get("booking_status", "not_started")

    if is_question and not is_booking_request:
        route = "faq"
    elif is_booking_request or status in {"in_progress", "pending_confirmation"}:
        route = "booking"
    else:
        route = "faq"
    update["route"] = route
    return update


async def faq_node(state: dict) -> dict:
    question = str(state["messages"][-1].content)
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is not configured. Add it to backend/.env.")

    documents = retrieve_handbook_context(question)
    excerpts = []
    citations = []
    for document in documents:
        page = int(document.metadata.get("page", 0)) + 1
        excerpts.append(f"[Employee Handbook, page {page}]\n{document.page_content}")
        citation = f"Employee Handbook, p. {page}"
        if citation not in citations:
            citations.append(citation)

    context = "\n\n".join(excerpts)
    model = ChatGroq(model="qwen/qwen3.8-27b", temperature=0)
    answer = await model.ainvoke(
        "Answer the employee's question using only the handbook excerpts below. "
        "If the excerpts do not contain the answer, say you could not find it in "
        "the handbook. Do not infer policy. Cite supporting pages in the answer.\n\n"
        f"Handbook excerpts:\n{context}\n\nQuestion: {question}"
    )
    response = str(answer.content)
    if citations and not any(citation in response for citation in citations):
        mentioned_citations = [
            citation
            for citation in citations
            if re.search(
                rf"\b(?:page|p\.?)\s*{re.search(r'\d+', citation).group()}\b",
                response,
                re.IGNORECASE,
            )
        ]
        response += "\n\nSource: " + "; ".join(mentioned_citations or citations)

    if state.get("booking_status") in {"in_progress", "pending_confirmation"}:
        response += "\n\nYour booking details are saved. "
        if state.get("booking_status") == "pending_confirmation":
            response += "Reply yes to confirm your selected slot, or no to choose another."
        elif state.get("selected_slot"):
            response += "Reply yes to confirm, or no to choose another appointment slot."
        else:
            response += "Choose an available appointment slot when you're ready."

    return {
        "assistant_response": response,
        "messages": [AIMessage(content=response)],
    }


def booking_node(state: dict) -> dict:
    message = str(state["messages"][-1].content).strip()
    name = state.get("user_name")
    email = state.get("user_email")
    status = state.get("booking_status", "not_started")
    slot = state.get("selected_slot")
    reference_id = state.get("reference_id")

    if status == "pending_confirmation":
        if message.casefold() in {"yes", "y", "confirm", "confirmed", "yes please"}:
            reference_id = confirmation_reference()
            status = "confirmed"
            response = (
                f"Your Performance Review is booked for {slot}. "
                f"Confirmation reference: {reference_id}."
            )
        elif message.casefold() in {"no", "n", "change", "another"}:
            slot = None
            status = "in_progress"
            response = "No problem. Choose another available slot:\n" + format_slots()
        else:
            response = f"Please reply yes to confirm {slot}, or no to choose another slot."
    elif not name or not email:
        status = "in_progress"
        missing = "your name and email" if not name and not email else (
            "your name" if not name else "your email"
        )
        response = f"Sure, I can help book a Performance Review. What is {missing}?"
    elif not slot:
        status = "in_progress"
        slot = selected_slot(message)
        if slot:
            slot = slot["label"]
            status = "pending_confirmation"
            response = f"Please confirm: book your Performance Review for {slot}? Reply yes or no."
        else:
            response = f"Thanks, {name}. Choose an available slot:\n{format_slots()}"
    else:
        status = "pending_confirmation"
        response = f"Please confirm: book your Performance Review for {slot}? Reply yes or no."

    return {
        "booking_status": status,
        "selected_slot": slot,
        "reference_id": reference_id,
        "assistant_response": response,
        "messages": [AIMessage(content=response)],
    }


def format_slots() -> str:
    return "\n".join(
        f"{index}. {slot['label']} ({slot['id']})"
        for index, slot in enumerate(available_slots(), start=1)
    )