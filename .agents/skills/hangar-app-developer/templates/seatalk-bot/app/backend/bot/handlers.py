from hangarkit.integrations import seatalk

from .replies import generate_bot_reply, send_and_record_reply
from .slash_commands import handle_slash_command
from .storage import record_handled_event, record_inbound_message, sync_thread_from_seatalk, update_handled_event

seatalk_listener = seatalk.listener()


REPLY_EVENT_TYPES = {
    seatalk.EVENT_MESSAGE_FROM_BOT_SUBSCRIBER,
    seatalk.EVENT_NEW_MENTIONED_MESSAGE_RECEIVED_FROM_GROUP_CHAT,
}


def should_reply(event: seatalk.WebhookEvent) -> bool:
    return event.event_type in REPLY_EVENT_TYPES


def callback_handler(event: seatalk.WebhookEvent):
    return seatalk_listener.handlers.get(event.event_type) or seatalk_listener.default_handler


async def handle_bot_event(event: seatalk.WebhookEvent, handler: str):
    record = record_handled_event(event, handler)
    try:
        inbound_record = record_inbound_message(event)
        thread_record = sync_thread_from_seatalk(event)
        reply = ""
        slash_command = None
        outbound_records = []
        reply_skipped = not should_reply(event)
        if should_reply(event):
            slash_command = await handle_slash_command(event)
            if slash_command:
                reply_skipped = True
            else:
                reply = await generate_bot_reply(event)
                outbound_records = await send_and_record_reply(event, reply)
                reply_skipped = not bool(outbound_records)
        update_handled_event(record, status="handled", processed=True, error="")
        return {
            "status": "ok",
            "event_type": event.event_type,
            "reply_sent": bool(outbound_records),
            "reply_skipped": reply_skipped,
            "slash_command": slash_command,
            "message": reply,
            "record": record,
            "inbound_message": inbound_record,
            "thread": thread_record,
            "outbound_messages": outbound_records,
        }
    except Exception as exc:
        update_handled_event(record, status="failed", processed=True, error=str(exc))
        raise


async def process_callback_event(event: seatalk.WebhookEvent):
    handler = callback_handler(event)
    if handler is None:
        return {"status": "ok", "event_type": event.event_type}
    result = await handler(event)
    if result is None:
        return {"status": "ok", "event_type": event.event_type}
    return result


@seatalk_listener.on(seatalk.EVENT_NEW_BOT_SUBSCRIBER)
async def handle_new_bot_subscriber(event: seatalk.WebhookEvent):
    return await handle_bot_event(event, "handle_new_bot_subscriber")


@seatalk_listener.on(seatalk.EVENT_USER_ENTER_CHATROOM_WITH_BOT)
async def handle_user_enter_chatroom_with_bot(event: seatalk.WebhookEvent):
    return await handle_bot_event(event, "handle_user_enter_chatroom_with_bot")


@seatalk_listener.on(seatalk.EVENT_MESSAGE_FROM_BOT_SUBSCRIBER)
async def handle_message_from_bot_subscriber(event: seatalk.WebhookEvent):
    return await handle_bot_event(event, "handle_message_from_bot_subscriber")


@seatalk_listener.on(seatalk.EVENT_NEW_MENTIONED_MESSAGE_RECEIVED_FROM_GROUP_CHAT)
async def handle_group_mention(event: seatalk.WebhookEvent):
    return await handle_bot_event(event, "handle_group_mention")


@seatalk_listener.on(seatalk.EVENT_NEW_MESSAGE_RECEIVED_FROM_THREAD)
async def handle_thread_message(event: seatalk.WebhookEvent):
    return await handle_bot_event(event, "handle_thread_message")


@seatalk_listener.on(seatalk.EVENT_BOT_ADDED_TO_GROUP_CHAT)
async def handle_bot_added_to_group_chat(event: seatalk.WebhookEvent):
    return await handle_bot_event(event, "handle_bot_added_to_group_chat")


@seatalk_listener.on(seatalk.EVENT_INTERACTIVE_MESSAGE_CLICK)
async def handle_interactive_message_click(event: seatalk.WebhookEvent):
    return await handle_bot_event(event, "handle_interactive_message_click")
