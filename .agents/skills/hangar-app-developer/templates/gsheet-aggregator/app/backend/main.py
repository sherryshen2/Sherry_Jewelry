from fastapi import APIRouter

import metrics
import scheduler
import store
import sync

router = APIRouter()


@router.get("/health")
def health():
    return {"ok": True, "sources": len(store.sources())}


@router.get("/sources")
def list_sources():
    return {"sources": store.sources()}


@router.post("/sources")
def update_source(payload: dict):
    source_id = str(payload.get("id") or "").strip()
    if not source_id:
        return {"ok": False, "error": "id is required"}
    patch = {
        key: payload[key]
        for key in [
            "name",
            "spreadsheet_url",
            "sheet_name",
            "range_name",
            "group_by",
            "value_field",
            "operation",
            "enabled",
        ]
        if key in payload
    }
    return {"ok": True, "source": store.save_source(source_id, patch)}


@router.post("/sync")
def run_sync(payload: dict | None = None):
    source_id = str((payload or {}).get("source_id") or "").strip()
    if source_id:
        return sync.sync_source(source_id)
    return sync.sync_all()


@router.get("/dashboard")
def dashboard():
    return metrics.dashboard()
