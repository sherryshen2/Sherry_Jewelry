from datetime import datetime, timezone

from hangarkit import ctx, table
from hangarkit.integrations import seatalk

from .event_helpers import actual_thread_id, conversation_key, event_id, event_summary, sender_from_webhook
from .schemas import EVENT_SCHEMA, GROUP_SCHEMA, MESSAGE_SCHEMA, THREAD_SCHEMA

MESSAGE_EVENT_TYPES = {
    seatalk.EVENT_MESSAGE_FROM_BOT_SUBSCRIBER,
    seatalk.EVENT_NEW_MENTIONED_MESSAGE_RECEIVED_FROM_GROUP_CHAT,
    seatalk.EVENT_NEW_MESSAGE_RECEIVED_FROM_THREAD,
    seatalk.EVENT_INTERACTIVE_MESSAGE_CLICK,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def first(value, *keys, default=""):
    current = value if isinstance(value, dict) else {}
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def text_from_message(message: dict) -> str:
    text = message.get("text") if isinstance(message, dict) else None
    if isinstance(text, str):
        return text
    if isinstance(text, dict):
        for key in ("plain_text", "content", "text", "markdown"):
            if text.get(key):
                return str(text.get(key))
    return ""


def sender_from_message(message: dict) -> dict:
    sender = message.get("sender") if isinstance(message, dict) else None
    if not isinstance(sender, dict):
        sender = {}
    return {
        "seatalk_id": str(sender.get("seatalk_id") or ""),
        "employee_code": str(sender.get("employee_code") or ""),
        "email": str(sender.get("email") or ""),
        "username": str(sender.get("username") or ""),
    }


def record_handled_event(event: seatalk.WebhookEvent, handler: str, status: str = "handled", error: str = ""):
    return table("seatalk_events").create(
        {
            "event_id": event_id(event),
            "event_type": event.event_type,
            "conversation_key": conversation_key(event),
            "employee_code": event.employee_code,
            "group_id": event.group_id,
            "thread_id": actual_thread_id(event),
            "message_id": event.message_id,
            "message_link": seatalk.format_message_link(event.message_id),
            "handler": handler,
            "summary": event_summary(event, handler),
            "status": status,
            "processed": False,
            "payload": event.payload,
            "error": error,
            "_schema": EVENT_SCHEMA,
        }
    )


def update_handled_event(record: dict | None, *, status: str | None = None, processed: bool | None = None, error: str | None = None):
    if not isinstance(record, dict):
        return None
    record_id = str(record.get("id") or "")
    if not record_id:
        return None

    patch = {}
    if status is not None:
        patch["status"] = status
    if processed is not None:
        patch["processed"] = processed
    if error is not None:
        patch["error"] = error
    if not patch:
        return record
    return table("seatalk_events").update(record_id, patch)


def record_message(
    event: seatalk.WebhookEvent,
    *,
    direction: str,
    status: str,
    text: str = "",
    message_id: str = "",
    payload=None,
    error: str = "",
):
    effective_message_id = message_id or event.message_id
    sender = {"bot": True, "app": ctx.app_slug} if direction == "outbound" else sender_from_webhook(event)
    return table("seatalk_messages").upsert(
        effective_message_id or event_id(event),
        {
            "conversation_key": conversation_key(event),
            "direction": direction,
            "event_type": event.event_type,
            "seatalk_message_id": effective_message_id,
            "message_link": seatalk.format_message_link(effective_message_id),
            "thread_id": actual_thread_id(event),
            "employee_code": event.employee_code,
            "group_id": event.group_id,
            "sender": sender,
            "text": text or event.text,
            "payload": payload if payload is not None else event.payload,
            "status": status,
            "error": error,
            "_schema": MESSAGE_SCHEMA,
        },
    )


def record_thread_message(event: seatalk.WebhookEvent, message: dict, status="synced"):
    message_id = str(message.get("message_id") or "")
    if not message_id:
        return None
    thread_id = str(message.get("thread_id") or actual_thread_id(event))
    group_id = str(event.group_id or message.get("group_id") or "")
    sender = sender_from_message(message)
    employee_code = sender.get("employee_code") or event.employee_code
    return table("seatalk_messages").upsert(
        message_id,
        {
            "conversation_key": f"thread:{thread_id}" if thread_id else conversation_key(event),
            "direction": "thread",
            "event_type": event.event_type,
            "seatalk_message_id": message_id,
            "message_link": seatalk.format_message_link(message_id),
            "thread_id": thread_id,
            "employee_code": employee_code,
            "group_id": group_id,
            "sender": sender,
            "text": text_from_message(message),
            "payload": message,
            "status": status,
            "error": "",
            "_schema": MESSAGE_SCHEMA,
        },
    )


def record_inbound_message(event: seatalk.WebhookEvent):
    if event.event_type not in MESSAGE_EVENT_TYPES:
        return None
    if not event.text and not event.message_id:
        return None
    return record_message(event, direction="inbound", status="received")


def record_thread_summary(event: seatalk.WebhookEvent, messages: list[dict], payload: dict, status="synced", error=""):
    thread_id = actual_thread_id(event)
    last_message = messages[-1] if messages else event.message
    return table("seatalk_threads").upsert(
        thread_id or event.message_id or event_id(event),
        {
            "thread_id": thread_id,
            "conversation_key": conversation_key(event),
            "group_id": event.group_id,
            "employee_code": event.employee_code,
            "source_event_id": event_id(event),
            "source_event_type": event.event_type,
            "message_count": len(messages),
            "last_message_id": str(last_message.get("message_id") or event.message_id or ""),
            "last_message_text": text_from_message(last_message) or event.text,
            "last_sender": sender_from_message(last_message) if isinstance(last_message, dict) else sender_from_webhook(event),
            "last_synced_at": utc_now(),
            "status": status,
            "error": error,
            "payload": payload,
            "_schema": THREAD_SCHEMA,
        },
    )


def extract_thread_messages(payload: dict) -> list[dict]:
    candidates = [
        payload.get("messages"),
        payload.get("message_list"),
        payload.get("thread_messages"),
        first(payload, "thread", "messages"),
        first(payload, "thread", "message_list"),
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]
    return []


def group_info_from_item(item: dict) -> dict:
    if not isinstance(item, dict):
        return {}
    for key in ("group_info", "group"):
        value = item.get(key)
        if isinstance(value, dict):
            return value
    return item


def group_member_count(info: dict) -> int:
    for key in ("group_user_total", "group_bot_total", "group_system_account_total"):
        value = info.get(key) if isinstance(info, dict) else None
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    users = info.get("group_user_list") if isinstance(info, dict) else []
    bots = info.get("group_bot_list") if isinstance(info, dict) else []
    system_accounts = info.get("group_system_account_list") if isinstance(info, dict) else []
    return sum(len(value) for value in (users, bots, system_accounts) if isinstance(value, list))


def sync_thread_from_seatalk(event: seatalk.WebhookEvent):
    thread_id = actual_thread_id(event)
    if not thread_id:
        return record_thread_summary(event, [event.message] if event.message else [], {"source": "webhook_no_thread"})

    try:
        if event.group_id:
            payload = seatalk.get_thread_by_thread_id(event.group_id, thread_id, page_size=50)
        elif event.employee_code:
            payload = seatalk.get_thread_by_thread_id_direct(event.employee_code, thread_id, page_size=50)
        else:
            payload = {"source": "webhook_only", "reason": "missing_group_or_employee"}

        messages = extract_thread_messages(payload)
        if not messages and event.message:
            messages = [event.message]
        for message in messages:
            record_thread_message(event, message)
        return record_thread_summary(event, messages, payload)
    except Exception as exc:
        payload = {"source": "get_thread_by_thread_id", "error": str(exc)}
        if event.message:
            record_thread_message(event, event.message, status="webhook_only")
        return record_thread_summary(event, [event.message] if event.message else [], payload, status="failed", error=str(exc))


def sync_joined_groups():
    groups = seatalk.get_all_joined_groups()
    records = []
    for item in groups:
        if not isinstance(item, dict):
            continue
        info = group_info_from_item(item)
        group_id = str(item.get("group_id") or info.get("group_id") or "")
        if not group_id:
            continue
        records.append(
            table("seatalk_groups").upsert(
                group_id,
                {
                    "group_id": group_id,
                    "group_name": str(info.get("group_name") or info.get("name") or group_id),
                    "member_count": group_member_count(info),
                    "payload": item,
                    "status": str(item.get("status") or "synced"),
                    "last_synced_at": utc_now(),
                    "error": str(item.get("error") or ""),
                    "_schema": GROUP_SCHEMA,
                },
            )
        )
    return records
