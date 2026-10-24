from datetime import date

from fastapi import APIRouter
from hangarkit import ctx, table

router = APIRouter()


def _parse_day(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


@router.get("/health")
def health():
    return {
        "status": "ok",
        "app": ctx.app_slug,
        "user": ctx.user_email,
        "request_id": ctx.request_id,
    }


@router.get("/summary")
def summary():
    tasks = table("tasks").list(sort="order", perPage=200)
    today = date.today()
    active = [task for task in tasks if str(task.get("status") or "") == "Active"]
    blocked = [task for task in tasks if str(task.get("status") or "") == "Blocked"]
    overdue = []
    for task in tasks:
        end_day = _parse_day(task.get("end_date"))
        status = str(task.get("status") or "")
        if end_day and end_day < today and status not in {"Complete", "Done"}:
            overdue.append(task)

    next_task = next((task for task in tasks if str(task.get("status") or "") in {"Active", "Blocked", "Ready"}), None)
    return {
        "count": len(tasks),
        "active": len(active),
        "blocked": len(blocked),
        "overdue": len(overdue),
        "lead": next_task.get("title") if next_task else "all clear",
        "message": f"{len(active)} active, {len(blocked)} blocked, {len(overdue)} overdue.",
    }


@router.get("/export-plan")
def export_plan():
    return {
        "tasks": table("tasks").list(sort="order", perPage=500),
        "milestones": table("milestones").list(sort="date", perPage=100),
    }
