import store


def _number(value):
    try:
        return float(value or 0)
    except Exception:
        return 0


def aggregate(rows, operation="sum"):
    groups = {}
    for row in rows:
        key = row.get("group") or "Uncategorized"
        current = groups.setdefault(key, {"label": key, "value": 0, "count": 0})
        current["value"] += _number(row.get("value"))
        current["count"] += 1

    output = []
    for item in groups.values():
        if operation == "avg" and item["count"]:
            item["value"] = item["value"] / item["count"]
        elif operation == "count":
            item["value"] = item["count"]
        output.append(item)

    return sorted(output, key=lambda item: item["label"])


def dashboard():
    sources = store.sources()
    rows = store.rows()
    active_source = sources[0] if sources else {}
    operation = active_source.get("operation") or "sum"
    chart = aggregate(rows, operation)
    total = sum(item["value"] for item in chart)
    return {
        "sources": sources,
        "rows": rows,
        "runs": store.recent_runs(),
        "chart": chart,
        "summary": {
            "source_count": len(sources),
            "row_count": len(rows),
            "total": total,
            "operation": operation,
        },
    }
