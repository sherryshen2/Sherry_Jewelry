from datetime import datetime, timezone
from importlib import import_module
import re
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from hangarkit import ctx, table

router = APIRouter()

tickets = table("tickets")
import_runs = table("import_runs")


class JiraSearchRequest(BaseModel):
    jql: str
    limit: int = 50


class JiraImportRequest(BaseModel):
    keys: List[str] = Field(default_factory=list)
    issues: List[Dict[str, Any]] = Field(default_factory=list)


def _integration(provider: str):
    integrations = import_module("hangarkit.integrations")
    try:
        return getattr(integrations, provider)
    except AttributeError:
        return import_module(f"hangarkit.integrations.{provider}")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_id(prefix: str, value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", str(value or "").lower()).strip("_")
    return f"{prefix}_{clean}"[:48] if clean else f"{prefix}_{int(datetime.now().timestamp())}"


def field_name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("displayName") or value.get("name") or value.get("value") or value.get("emailAddress") or "")
    return str(value or "")


def field_email(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("emailAddress") or value.get("email") or "")
    return ""


def issue_url(key: str) -> str:
    return f"https://jira.shopee.io/browse/{key}"


def normalize_priority(value: str) -> str:
    text = str(value or "").lower()
    if "block" in text or "urgent" in text or text in {"p0", "critical", "highest"}:
        return "urgent"
    if "high" in text or text == "p1":
        return "high"
    if "low" in text or text in {"p3", "p4"}:
        return "low"
    return "medium"


def normalize_status(value: str) -> str:
    text = str(value or "").lower()
    if "done" in text or "closed" in text:
        return "closed"
    if "resolve" in text or "fixed" in text:
        return "resolved"
    if "wait" in text or "blocked" in text or "hold" in text:
        return "waiting"
    if "progress" in text or "dev" in text or "doing" in text:
        return "in_progress"
    if "triage" in text or "review" in text:
        return "triage"
    return "open"


def normalize_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    fields = issue.get("fields") if isinstance(issue.get("fields"), dict) else issue
    key = str(issue.get("key") or fields.get("key") or "").upper()
    assignee = fields.get("assignee") or {}
    reporter = fields.get("reporter") or {}
    status_name = field_name(fields.get("status") or fields.get("status_name"))
    priority_name = field_name(fields.get("priority") or fields.get("priority_name"))
    updated_at = str(fields.get("updated") or issue.get("updated") or now_iso())
    created_at = str(fields.get("created") or issue.get("created") or updated_at)
    summary = str(fields.get("summary") or issue.get("summary") or key or "Jira issue")
    description = fields.get("description") or issue.get("description") or ""
    if isinstance(description, dict):
        description = str(description)
    return {
        "key": key,
        "subject": summary,
        "summary": summary,
        "description": str(description or ""),
        "status": normalize_status(status_name or issue.get("status")),
        "status_name": status_name,
        "priority": normalize_priority(priority_name or issue.get("priority")),
        "priority_name": priority_name,
        "assignee": field_name(assignee) or str(issue.get("assignee") or ""),
        "assignee_email": field_email(assignee),
        "reporter": field_name(reporter),
        "requester_email": field_email(reporter),
        "issue_type": field_name(fields.get("issuetype") or fields.get("issue_type")),
        "updated": updated_at,
        "created": created_at,
        "url": str(issue.get("url") or issue_url(key)),
        "labels": fields.get("labels") or issue.get("labels") or [],
    }


def ticket_from_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    item = normalize_issue(issue)
    return {
        "subject": item["subject"],
        "description": item["description"] or f"Imported from Jira {item['key']}.",
        "status": item["status"],
        "priority": item["priority"],
        "requester_name": item["reporter"],
        "requester_email": item["requester_email"],
        "assignee_id": "",
        "assignee_name": item["assignee"],
        "assignee_email": item["assignee_email"],
        "source": "jira",
        "jira_key": item["key"],
        "jira_url": item["url"],
        "jira_status": item["status_name"],
        "jira_priority": item["priority_name"],
        "issue_type": item["issue_type"],
        "labels": item["labels"],
        "created_at": item["created"],
        "updated_at": item["updated"],
        "last_synced_at": now_iso(),
    }


def serialize_ticket(record: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(record or {})
    data["labels"] = data.get("labels") or []
    return data


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
    rows = tickets.list(sort="-updated_at", perPage=200)
    open_rows = [row for row in rows if str(row.get("status") or "").lower() not in ["closed", "resolved"]]
    urgent_rows = [row for row in rows if str(row.get("priority") or "").lower() == "urgent"]
    return {
        "count": len(rows),
        "open": len(open_rows),
        "urgent": len(urgent_rows),
        "lead": open_rows[0].get("subject") if open_rows else "all clear",
    }


@router.get("/jira/my-issues")
def my_jira_issues(max_results: int = Query(30, ge=1, le=100)):
    try:
        raw = _integration("jira").search_my_open_issues(max_results=max_results)
    except TypeError:
        raw = _integration("jira").search_my_open_issues(limit=max_results)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Jira assigned issue lookup failed: {exc}") from exc
    issues = [normalize_issue(item) for item in (raw or [])]
    return {"issues": issues, "count": len(issues)}


@router.post("/jira/search")
def search_jira(req: JiraSearchRequest):
    if not req.jql.strip():
        raise HTTPException(status_code=400, detail="JQL is required")
    fields = ["summary", "status", "assignee", "reporter", "updated", "created", "priority", "issuetype", "labels", "description"]
    try:
        raw = _integration("jira").search_all(req.jql, limit=min(req.limit, 100), fields=fields)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Jira search failed: {exc}") from exc
    issues = [normalize_issue(item) for item in (raw or [])]
    return {"issues": issues, "count": len(issues)}


@router.post("/jira/import")
def import_jira(req: JiraImportRequest):
    selected = {str(key).upper() for key in req.keys if str(key).strip()}
    issues = [issue for issue in req.issues if not selected or str(issue.get("key") or "").upper() in selected]

    missing = [key for key in selected if key not in {str(issue.get("key") or "").upper() for issue in issues}]
    if missing:
        jira = _integration("jira")
        for key in missing:
            try:
                issues.append(jira.get_issue(key))
            except Exception:
                pass

    imported = 0
    updated = 0
    saved = []
    for issue in issues:
        payload = ticket_from_issue(issue)
        key = payload.get("jira_key")
        if not key:
            continue
        record_id = safe_id("jira", key)
        try:
            existing = tickets.get(record_id)
        except Exception:
            existing = None
        record = tickets.upsert(record_id, payload)
        if existing:
            updated += 1
        else:
            imported += 1
        saved.append(serialize_ticket(record))

    run = import_runs.create(
        {
            "source": "jira",
            "created_at": now_iso(),
            "created_by": ctx.user_email or ctx.user or "hangar",
            "query": "assigned_to_me" if not req.issues else "selected_preview",
            "selected_keys": sorted(selected),
            "imported_count": imported,
            "updated_count": updated,
            "result_count": len(saved),
        }
    )

    return {"imported": imported, "updated": updated, "tickets": saved, "run": run}


@router.get("/mail/requester-context")
def requester_context(email: str = Query("")):
    clean = email.strip()
    if not clean:
        raise HTTPException(status_code=400, detail="Requester email is required")
    try:
        google_mail = _integration("google_mail")
        raw = google_mail.search_messages(f"from:{clean} OR to:{clean} newer_than:30d", max_results=5)
    except Exception as exc:
        return {"ok": False, "message": f"Google Mail is not ready: {exc}", "messages": []}
    return {"ok": True, "message": "Recent requester mail loaded.", "messages": raw or []}
