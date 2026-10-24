import hashlib
import json

import sheets
import store


def _clean_header(value, fallback):
    text = str(value or "").strip()
    return text or fallback


def _number(value):
    text = str(value or "").replace(",", "").replace("$", "").strip()
    try:
        return float(text)
    except Exception:
        return 0


def rows_from_values(source, values):
    if not values:
        return []

    headers = [_clean_header(value, f"Column {index + 1}") for index, value in enumerate(values[0])]
    group_by = str(source.get("group_by") or headers[0]).strip()
    value_field = str(source.get("value_field") or headers[min(2, len(headers) - 1)]).strip()
    output = []

    for offset, values_row in enumerate(values[1:], start=2):
        raw = {header: values_row[index] if index < len(values_row) else "" for index, header in enumerate(headers)}
        row_key = hashlib.sha1(json.dumps(raw, sort_keys=True).encode("utf-8")).hexdigest()[:16]
        output.append(
            {
                "id": f"{source['id']}-{row_key}",
                "source_id": source["id"],
                "row_key": row_key,
                "row_index": offset,
                "group": str(raw.get(group_by) or "Uncategorized"),
                "label": str(raw.get(headers[0]) or f"Row {offset}"),
                "value": _number(raw.get(value_field)),
                "raw": raw,
                "synced_at": store.now_iso(),
            }
        )

    return output


def sync_source(source_id):
    source = store.source(source_id)
    started_at = store.now_iso()
    try:
        values = sheets.read_values(source)
        rows = rows_from_values(source, values)
        for row in rows:
            store.upsert_row(row["id"], row)

        completed_at = store.now_iso()
        store.save_source(
            source_id,
            {
                "last_synced_at": completed_at,
                "last_status": "Synced",
                "last_error": "",
            },
        )
        store.create_run(
            {
                "source_id": source_id,
                "started_at": started_at,
                "completed_at": completed_at,
                "status": "success",
                "rows_read": max(len(values) - 1, 0),
                "rows_saved": len(rows),
                "error": "",
            }
        )
        return {"ok": True, "source_id": source_id, "rows_read": max(len(values) - 1, 0), "rows_saved": len(rows)}
    except Exception as exc:
        completed_at = store.now_iso()
        message = str(exc)
        store.save_source(source_id, {"last_synced_at": completed_at, "last_status": "Error", "last_error": message})
        store.create_run(
            {
                "source_id": source_id,
                "started_at": started_at,
                "completed_at": completed_at,
                "status": "error",
                "rows_read": 0,
                "rows_saved": 0,
                "error": message,
            }
        )
        return {"ok": False, "source_id": source_id, "error": message}


def sync_all():
    results = []
    for source in store.sources():
        if source.get("enabled") is False:
            continue
        results.append(sync_source(source["id"]))
    return {"ok": all(item.get("ok") for item in results), "results": results}
