from datetime import datetime, timezone

from hangarkit import table


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def sources():
    return table("sheet_sources").list()


def source(source_id):
    return table("sheet_sources").get(source_id)


def save_source(source_id, patch):
    return table("sheet_sources").update(source_id, patch)


def rows(source_id=None):
    items = table("sheet_rows").list()
    if source_id:
        return [row for row in items if row.get("source_id") == source_id]
    return items


def upsert_row(row_id, row):
    return table("sheet_rows").upsert(row_id, row)


def create_run(run):
    return table("sync_runs").create(run)


def recent_runs(limit=8):
    runs = table("sync_runs").list()
    return sorted(runs, key=lambda item: item.get("started_at") or "", reverse=True)[:limit]
