from hangarkit.integrations import seatalk


def actual_thread_id(event: seatalk.WebhookEvent) -> str:
    return str(event.message.get("thread_id") or event.message_id or "")


def conversation_key(event: seatalk.WebhookEvent) -> str:
    thread_id = actual_thread_id(event)
    if thread_id:
        return f"thread:{thread_id}"
    if event.group_id:
        return f"group:{event.group_id}"
    if event.employee_code:
        return f"subscriber:{event.employee_code}"
    return f"event:{event.event_type}"


def event_id(event: seatalk.WebhookEvent) -> str:
    return str(
        event.payload.get("event_id")
        or event.payload.get("eventId")
        or event.payload.get("uuid")
        or event.message_id
        or ""
    )


def event_summary(event: seatalk.WebhookEvent, handler: str) -> str:
    if event.text:
        return event.text[:240]
    if event.employee_code:
        return f"{handler} for employee {event.employee_code}"
    if event.group_id:
        return f"{handler} for group {event.group_id}"
    return handler


def sender_from_webhook(event: seatalk.WebhookEvent) -> dict:
    sender = event.sender if isinstance(event.sender, dict) else {}
    return {
        "seatalk_id": str(sender.get("seatalk_id") or ""),
        "employee_code": str(sender.get("employee_code") or ""),
        "email": str(sender.get("email") or ""),
    }
