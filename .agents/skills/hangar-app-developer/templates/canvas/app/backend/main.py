from fastapi import APIRouter
from hangarkit import ctx, table

router = APIRouter()

PRIMARY_TABLE = "notes"
TITLE_FIELD = "title"
STATUS_FIELD = "status"


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
    rows = table(PRIMARY_TABLE).list(sort="-created", perPage=100)
    open_rows = [
        row
        for row in rows
        if str(row.get(STATUS_FIELD) or "").lower() not in ["done", "closed", "resolved", "completed", "published"]
    ]
    lead = open_rows[0].get(TITLE_FIELD) if open_rows else "all clear"
    return {
        "count": len(rows),
        "open": len(open_rows),
        "lead": lead,
        "message": f"{len(open_rows)} open record{'s' if len(open_rows) != 1 else ''}; next focus is {lead}.",
    }
