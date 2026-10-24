from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from hangarkit import table


GRANULARITIES = {"hourly", "daily", "weekly", "monthly"}
LIMITS = {"hourly": 48, "daily": 30, "weekly": 16, "monthly": 12}


def _as_datetime(value: Any) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    except ValueError:
        return None


def _bucket_key(value: Any, granularity: str) -> str:
    moment = _as_datetime(value)
    if not moment:
        return "Unknown"
    moment = moment.astimezone(timezone.utc)
    if granularity == "hourly":
        return moment.strftime("%Y-%m-%d %H:00")
    if granularity == "weekly":
        return (moment - timedelta(days=moment.weekday())).date().isoformat()
    if granularity == "monthly":
        return moment.strftime("%Y-%m")
    return moment.date().isoformat()


def metrics(granularity: str = "daily") -> dict[str, Any]:
    granularity = granularity if granularity in GRANULARITIES else "daily"
    tasks = table("smart_workflow_tasks").list(sort="-created", perPage=1000)
    buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {"total": 0, "success": 0, "failed": 0, "running": 0, "provider_cost": Decimal("0")})
    successful = failed = running = terminal = 0
    durations: list[float] = []
    provider_cost_total = Decimal("0")
    for task in tasks:
        status = str(task.get("status") or "queued").lower()
        bucket = buckets[_bucket_key(task.get("started_at") or task.get("created"), granularity)]
        bucket["total"] += 1
        cost = Decimal(str(task.get("provider_cost") or 0))
        provider_cost_total += cost
        bucket["provider_cost"] += cost
        if status == "success":
            successful += 1; terminal += 1; bucket["success"] += 1
        elif status == "failed":
            failed += 1; terminal += 1; bucket["failed"] += 1
        else:
            running += 1; bucket["running"] += 1
        if task.get("duration_ms") is not None:
            durations.append(float(task["duration_ms"]))
    series = [{"label": label, **values, "provider_cost": format(values["provider_cost"], "f")} for label, values in sorted(buckets.items())[-LIMITS[granularity]:]]
    return {
        "granularity": granularity, "total": len(tasks), "terminal": terminal, "successful": successful, "failed": failed, "running": running,
        "success_rate": successful / terminal if terminal else 0, "average_duration_ms": sum(durations) / len(durations) if durations else 0,
        "provider_cost_total": format(provider_cost_total, "f"), "average_provider_cost": format(provider_cost_total / len(tasks), "f") if tasks else "0", "series": series,
    }
