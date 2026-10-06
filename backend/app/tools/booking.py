import re
import secrets
from datetime import datetime, timedelta, timezone


def available_slots() -> list[dict[str, str]]:
    slots = []
    day = datetime.now(timezone.utc).date() + timedelta(days=1)
    while len(slots) < 3:
        if day.weekday() < 5:
            index = len(slots) + 1
            hour = (10, 13, 15)[len(slots)]
            label = datetime.combine(day, datetime.min.time()).replace(
                hour=hour, tzinfo=timezone.utc
            ).strftime("%A, %B %d at %I:%M %p UTC").replace(" 0", " ")
            slots.append({"id": f"slot-{index}", "label": label})
        day += timedelta(days=1)
    return slots


def extract_contact(message: str) -> tuple[str | None, str | None]:
    email_match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", message)
    email = email_match.group(0) if email_match else None
    name = None

    named = re.search(
        r"(?:my name is|name is|i am|i'm)\s+([A-Za-z][A-Za-z'-]*(?:\s+[A-Za-z][A-Za-z'-]*){0,2})",
        message,
        re.IGNORECASE,
    )
    if named:
        name = named.group(1).strip()
    elif email_match:
        prefix = message[: email_match.start()].strip(" ,;:.-")
        prefix = re.sub(r"^(?:hi[, ]+|hello[, ]+)", "", prefix, flags=re.IGNORECASE)
        candidate = re.match(
            r"([A-Za-z][A-Za-z'-]*(?:\s+[A-Za-z][A-Za-z'-]*){0,2})\s*$",
            prefix,
        )
        if candidate:
            name = candidate.group(1).strip()
    else:
        candidate = re.fullmatch(
            r"\s*([A-Za-z][A-Za-z'-]*(?:\s+[A-Za-z][A-Za-z'-]*){0,2})\s*",
            message,
        )
        if candidate:
            name = candidate.group(1).strip()

    return name, email


def selected_slot(message: str) -> dict[str, str] | None:
    normalized = message.casefold().strip()
    slots = available_slots()
    for slot in slots:
        if slot["id"] in normalized or slot["label"].casefold() in normalized:
            return slot
    if normalized in {"1", "2", "3"}:
        return slots[int(normalized) - 1]
    return None


def confirmation_reference() -> str:
    return f"PR-{secrets.token_hex(3).upper()}"