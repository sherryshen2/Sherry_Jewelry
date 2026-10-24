from fastapi import APIRouter
from hangarkit import ctx, table

router = APIRouter()


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
    tasks = table("tasks").list(sort="-created", perPage=100)
    notes = table("notes").list(sort="-created", perPage=20)
    open_tasks = [task for task in tasks if not task.get("done")]
    top_area = "Personal"
    if open_tasks:
        counts = {}
        for task in open_tasks:
            area = task.get("area") or "Personal"
            counts[area] = counts.get(area, 0) + 1
        top_area = sorted(counts.items(), key=lambda item: item[1], reverse=True)[0][0]

    return {
        "open_tasks": len(open_tasks),
        "notes": len(notes),
        "top_area": top_area,
        "message": f"{len(open_tasks)} open focus items, led by {top_area}. {len(notes)} recent notes are ready for review.",
    }


@router.post("/capture")
def capture(payload: dict):
    title = str(payload.get("title") or "Untitled").strip()
    body = str(payload.get("body") or title).strip()
    created = table("notes").create(
        {
            "title": title,
            "body": body,
            "mood": str(payload.get("mood") or "Clear"),
            "_schema": [
                {"name": "title", "type": "text", "required": True},
                {"name": "body", "type": "text"},
                {"name": "mood", "type": "text"},
            ],
        }
    )
    return {"created": created, "request_id": ctx.request_id}
