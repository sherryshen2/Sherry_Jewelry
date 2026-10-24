import asyncio
import traceback

from fastapi import APIRouter, HTTPException, Request
from hangarkit import ctx, table
from hangarkit.integrations import seatalk

from .event_helpers import conversation_key
from .handlers import process_callback_event, seatalk_listener
from .replies import send_and_record_reply
from .storage import sync_joined_groups, sync_thread_from_seatalk

router = APIRouter()
BACKGROUND_CALLBACK_TASKS: set[asyncio.Task] = set()


async def run_callback_task(event: seatalk.WebhookEvent):
    try:
        await process_callback_event(event)
    except Exception:
        traceback.print_exc()


def schedule_callback_task(event: seatalk.WebhookEvent):
    task = asyncio.create_task(run_callback_task(event))
    BACKGROUND_CALLBACK_TASKS.add(task)
    task.add_done_callback(BACKGROUND_CALLBACK_TASKS.discard)


@router.get("/health")
def health():
    return {
        "status": "ok",
        "configured": seatalk.configured(),
        "app": ctx.app_slug,
        "request_id": ctx.request_id,
        "handled_event_types": list(seatalk_listener.handlers.keys()),
    }


@router.post("/seatalk/callback")
async def seatalk_callback(request: Request):
    try:
        event = await seatalk.read_webhook_event(request)
    except seatalk.SeaTalkError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if event.event_type == seatalk.EVENT_VERIFICATION:
        return {"seatalk_challenge": event.challenge}

    schedule_callback_task(event)
    return {"status": "accepted", "event_type": event.event_type}


@router.get("/seatalk/groups/sync")
def sync_groups():
    records = sync_joined_groups()
    return {"ok": True, "count": len(records), "groups": records}


@router.post("/seatalk/thread/sync")
def sync_thread(payload: dict):
    group_id = str(payload.get("group_id") or "")
    employee_code = str(payload.get("employee_code") or "")
    thread_id = str(payload.get("thread_id") or payload.get("message_id") or "")
    message_id = str(payload.get("message_id") or thread_id)
    if not thread_id:
        raise HTTPException(status_code=400, detail="Missing thread_id")

    event_payload = {
        "event_id": payload.get("event_id") or f"manual-sync-{thread_id}",
        "event_type": payload.get("event_type") or seatalk.EVENT_NEW_MESSAGE_RECEIVED_FROM_THREAD,
        "event": {
            "group_id": group_id,
            "employee_code": employee_code,
            "message": {
                "message_id": message_id,
                "thread_id": thread_id,
                "sender": payload.get("sender") or {},
                "text": {"plain_text": payload.get("text") or ""},
            },
        },
    }
    event = seatalk.parse_webhook_payload(event_payload)
    record = sync_thread_from_seatalk(event)
    return {"ok": True, "thread": record}


@router.post("/seatalk/mark-processed")
def mark_processed(payload: dict):
    event_id_value = str(payload.get("id") or "").strip()
    if not event_id_value:
        raise HTTPException(status_code=400, detail="Missing event id")

    updated = table("seatalk_events").update(event_id_value, {"processed": True})
    return {"updated": updated}


@router.post("/seatalk/reply")
async def reply(payload: dict):
    text = str(payload.get("text") or "").strip()
    thread_id = str(payload.get("thread_id") or payload.get("message_id") or "")
    group_id = str(payload.get("group_id") or "")
    employee_code = str(payload.get("employee_code") or "")
    if not text:
        raise HTTPException(status_code=400, detail="Missing reply text")
    if not group_id and not employee_code:
        raise HTTPException(status_code=400, detail="Missing group_id or employee_code")

    event_payload = {
        "event_id": payload.get("event_id") or f"manual-reply-{thread_id or employee_code}",
        "event_type": payload.get("event_type") or seatalk.EVENT_NEW_MESSAGE_RECEIVED_FROM_THREAD,
        "event": {
            "group_id": group_id,
            "employee_code": employee_code,
            "message": {
                "message_id": str(payload.get("message_id") or thread_id),
                "thread_id": thread_id,
                "sender": payload.get("sender") or {},
                "text": {"plain_text": text},
            },
        },
    }
    event = seatalk.parse_webhook_payload(event_payload)
    records = await send_and_record_reply(event, text)
    return {"ok": True, "conversation_key": conversation_key(event), "messages": records}
