EVENT_SCHEMA = [
    {"name": "event_id", "type": "text"},
    {"name": "event_type", "type": "text"},
    {"name": "conversation_key", "type": "text"},
    {"name": "employee_code", "type": "text"},
    {"name": "group_id", "type": "text"},
    {"name": "thread_id", "type": "text"},
    {"name": "message_id", "type": "text"},
    {"name": "message_link", "type": "url"},
    {"name": "handler", "type": "text"},
    {"name": "summary", "type": "text"},
    {"name": "status", "type": "text", "default": "handled"},
    {"name": "processed", "type": "boolean", "default": False},
    {"name": "payload", "type": "json"},
    {"name": "error", "type": "text"},
]

MESSAGE_SCHEMA = [
    {"name": "conversation_key", "type": "text"},
    {"name": "direction", "type": "text"},
    {"name": "event_type", "type": "text"},
    {"name": "seatalk_message_id", "type": "text"},
    {"name": "message_link", "type": "url"},
    {"name": "thread_id", "type": "text"},
    {"name": "employee_code", "type": "text"},
    {"name": "group_id", "type": "text"},
    {"name": "sender", "type": "json"},
    {"name": "text", "type": "text"},
    {"name": "payload", "type": "json"},
    {"name": "status", "type": "text", "default": "received"},
    {"name": "error", "type": "text"},
]

THREAD_SCHEMA = [
    {"name": "thread_id", "type": "text"},
    {"name": "conversation_key", "type": "text"},
    {"name": "group_id", "type": "text"},
    {"name": "employee_code", "type": "text"},
    {"name": "source_event_id", "type": "text"},
    {"name": "source_event_type", "type": "text"},
    {"name": "message_count", "type": "number", "default": 0},
    {"name": "last_message_id", "type": "text"},
    {"name": "last_message_text", "type": "text"},
    {"name": "last_sender", "type": "json"},
    {"name": "last_synced_at", "type": "date"},
    {"name": "status", "type": "text", "default": "synced"},
    {"name": "error", "type": "text"},
    {"name": "payload", "type": "json"},
]

GROUP_SCHEMA = [
    {"name": "group_id", "type": "text"},
    {"name": "group_name", "type": "text"},
    {"name": "member_count", "type": "number", "default": 0},
    {"name": "payload", "type": "json"},
    {"name": "status", "type": "text", "default": "synced"},
    {"name": "last_synced_at", "type": "date"},
    {"name": "error", "type": "text"},
]
