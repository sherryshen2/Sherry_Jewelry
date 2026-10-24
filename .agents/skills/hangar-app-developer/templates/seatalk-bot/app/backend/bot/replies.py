import asyncio
import hashlib
from time import monotonic
from uuid import uuid4

from hangarkit.integrations import llm_chat, seatalk, wingman_chat

from .event_helpers import actual_thread_id, sender_from_webhook
from .skills import active_agent_skills, build_agent_message, build_agent_skill_prompt
from .storage import record_message


CHAT_PROVIDER = "llm_chat"  # Change to "wingman_chat" to use the managed Wingman agent.


def response_content(response) -> str:
    if isinstance(response, dict):
        choices = response.get("choices")
        if isinstance(choices, list) and choices:
            choice = choices[0] if isinstance(choices[0], dict) else {}
            message = choice.get("message") if isinstance(choice, dict) else {}
            if isinstance(message, dict) and message.get("content") is not None:
                return str(message.get("content") or "")
        content = response.get("content")
        if content is None and isinstance(response.get("message"), dict):
            content = response["message"].get("content")
        if content is None and isinstance(response.get("data"), dict):
            content = response["data"].get("content")
        return str(content or "")
    return str(response or "")


async def generate_bot_reply(event: seatalk.WebhookEvent) -> str:
    text = (event.text or "").strip()
    if not text:
        return ""

    sender = sender_from_webhook(event)
    skills = active_agent_skills()
    skill_prompt = build_agent_skill_prompt(skills)
    provider = CHAT_PROVIDER if CHAT_PROVIDER in {"wingman_chat", "llm_chat"} else "llm_chat"
    metadata = {
        "source": "hangar_seatalk_bot",
        "event_type": event.event_type,
        "group_id": event.group_id,
        "thread_id": actual_thread_id(event),
        "employee_code": event.employee_code,
        "message_id": event.message_id,
        "sender": sender,
        "skills": [{"id": skill["id"], "title": skill["title"]} for skill in skills],
        "group_setting": {
            "group_prompt": skill_prompt,
            "use_group_prompt_only": False,
        } if skill_prompt else {},
    }
    prompt = build_agent_message(text, skill_prompt)
    if provider == "llm_chat":
        response = llm_chat.chat_completions.create(
            messages=[{"role": "user", "content": prompt}],
        )
    else:
        turn_key = (
            hashlib.sha256(f"{event.group_id}:{event.message_id}".encode()).hexdigest()
            if event.message_id else str(uuid4())
        )
        run = await asyncio.to_thread(
            wingman_chat.start,
            prompt,
            metadata=metadata,
            idempotency_key=turn_key,
            timeout=300,
        )
        run_id = run["run_id"]
        deadline = monotonic() + 330
        while monotonic() < deadline:
            status = await asyncio.to_thread(wingman_chat.get_run, run_id)
            if status["status"] == "completed":
                return response_content(status["result"])
            if status["status"] == "failed":
                raise RuntimeError(status.get("error") or "Wingman Chat run failed")
            await asyncio.sleep(2)
        raise TimeoutError(f"Wingman Chat run {run_id} did not finish")
    return response_content(response)


async def send_and_record_reply(event: seatalk.WebhookEvent, text: str):
    if not text:
        return []

    try:
        if event.group_id:
            sent = seatalk.send_text_chunks_to_group(
                event.group_id,
                text,
                thread_id=actual_thread_id(event),
            )
        else:
            sent = seatalk.send_text_chunks_to_subscriber(
                event.employee_code,
                text,
            )

        records = []
        for result in sent:
            records.append(
                record_message(
                    event,
                    direction="outbound",
                    status="sent",
                    text=result.get("text", ""),
                    message_id=result.get("message_id", ""),
                    payload=result,
                )
            )
        return records
    except Exception as exc:
        record_message(event, direction="outbound", status="failed", text=text, error=str(exc), payload={"text": text})
        raise
