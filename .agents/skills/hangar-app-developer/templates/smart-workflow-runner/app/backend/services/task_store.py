from datetime import datetime, timezone
import json
from typing import Any, Optional

from hangarkit import ctx, table

TASKS = table("smart_workflow_tasks")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def compact_input(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("data:") and ";base64," in value:
        prefix, encoded = value.split(",", 1)
        return {"kind": "file", "mime_type": prefix[5:].split(";", 1)[0], "encoded_bytes": len(encoded)}
    if isinstance(value, dict):
        return {str(key): compact_input(item) for key, item in value.items()}
    if isinstance(value, list):
        return [compact_input(item) for item in value]
    return value


def generated_title(input_variables: dict[str, Any]) -> str:
    """Create a compact, useful task label when the user leaves title blank."""
    values: list[str] = []
    for value in input_variables.values():
        if value is None:
            continue
        if isinstance(value, bool):
            text = "true" if value else "false"
        elif isinstance(value, (dict, list)):
            text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        else:
            text = str(value)
        text = text.strip()
        if text:
            values.append(text[:20])
    return ", ".join(values) or "SMART workflow run"


def create_task(title: str, input_variables: dict[str, Any], file_assets: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
    started_at = now()
    input_summary = compact_input(input_variables)
    return TASKS.create({
        "title": title.strip() or generated_title(input_variables),
        "status": "queued",
        "submitted_by": ctx.user_email or ctx.user or "Hangar user",
        "input_variables": input_summary,
        "input_summary": input_summary,
        "file_assets": file_assets or [],
        "error_messages": [],
        "started_at": started_at,
        "attempt": 1,
        "progress_percent": 0,
        "progress_summary": {"total_nodes": 0, "completed_nodes": 0, "running_nodes": 0},
        "provider_cost": None,
        "smart_usage": {},
        "parsed_progress": {"nodes": []},
    })


def get_task(task_id: str) -> dict[str, Any]:
    task = TASKS.get(task_id)
    if not isinstance(task, dict):
        raise KeyError("Task not found")
    return task


def update_task(task_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    return TASKS.update(task_id, patch)
