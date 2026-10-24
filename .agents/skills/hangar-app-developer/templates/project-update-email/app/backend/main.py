from datetime import datetime, timedelta, timezone
from html import escape
from importlib import import_module
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from hangarkit import app_url, ctx, table

router = APIRouter()
runs = table("runs")
email_preferences = table("email_preferences")


class ProjectUpdateRequest(BaseModel):
    jira: str = ""
    epic_key: str = ""
    compare_mode: str = "last"
    compare_since: str = ""
    recipients: List[str] = Field(default_factory=list)


class SendEmailRequest(BaseModel):
    recipients: List[str] = Field(default_factory=list)
    subject: str = ""


def _integration(provider: str):
    integrations = import_module("hangarkit.integrations")
    try:
        return getattr(integrations, provider)
    except AttributeError:
        return import_module(f"hangarkit.integrations.{provider}")


def _email():
    return import_module("hangarkit").email


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_time(value: str) -> datetime:
    text = str(value or "").strip()
    if not text:
        return datetime.now(timezone.utc) - timedelta(days=7)
    if len(text) == 10:
        text = text + "T00:00:00+00:00"
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    if len(text) > 5 and (text[-5] in ["+", "-"]) and text[-3] != ":":
        text = text[:-2] + ":" + text[-2:]
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return datetime.now(timezone.utc) - timedelta(days=7)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def jira_time(value: str) -> str:
    return parse_time(value).strftime("%Y-%m-%d %H:%M")


def jql_quote(value: str) -> str:
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def jira_key(value: str) -> str:
    text = str(value or "").strip().upper()
    match = re.search(r"(?:BROWSE/)?([A-Z][A-Z0-9]+-\d+)", text)
    return match.group(1) if match else text


def preference_id(key: str) -> str:
    return jira_key(key).lower().replace("-", "_")


def epic_jql(epic_key: str) -> str:
    quoted = jql_quote(epic_key)
    return f'("Epic Link" = {quoted} OR parent = {quoted}) ORDER BY updated DESC'


def issue_url(key: str) -> str:
    return f"https://jira.shopee.io/browse/{key}"


def field_name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("displayName") or value.get("name") or value.get("value") or "")
    return str(value or "")


def summarize_issue(issue: Dict[str, Any], since: datetime) -> Dict[str, Any]:
    fields = issue.get("fields") or {}
    created = str(fields.get("created") or "")
    updated = str(fields.get("updated") or "")
    created_dt = parse_time(created)
    updated_dt = parse_time(updated)
    key = str(issue.get("key") or "")
    return {
        "key": key,
        "url": issue_url(key),
        "summary": str(fields.get("summary") or ""),
        "status": field_name(fields.get("status")),
        "assignee": field_name(fields.get("assignee")),
        "priority": field_name(fields.get("priority")),
        "issue_type": field_name(fields.get("issuetype")),
        "created": created,
        "updated": updated,
        "is_new": created_dt >= since,
        "was_updated": updated_dt >= since,
    }


def latest_run_for_epic(epic_key: str) -> Optional[Dict[str, Any]]:
    items = runs.list(filter=f'epic_key = "{epic_key}"', sort="-created_at", perPage=25)
    return items[0] if items else None


def save_recipients(epic_key: str, recipients: List[str]):
    clean = [item.strip() for item in recipients if item and item.strip()]
    if not epic_key or not clean:
        return None
    return email_preferences.upsert(
        preference_id(epic_key),
        {
            "jira_key": epic_key,
            "recipients": clean,
            "updated_at": now_iso(),
            "updated_by": ctx.user_email or ctx.user or "hangar",
        },
    )


def saved_recipients(epic_key: str) -> List[str]:
    if not epic_key:
        return []
    try:
        record = email_preferences.get(preference_id(epic_key))
        recipients = record.get("recipients") if isinstance(record, dict) else []
        return recipients if isinstance(recipients, list) else []
    except Exception:
        return []


def compare_since_for_request(req: ProjectUpdateRequest) -> str:
    if req.compare_mode == "date" and req.compare_since:
        return parse_time(req.compare_since).isoformat()
    previous = latest_run_for_epic(jira_key(req.jira or req.epic_key))
    if previous and previous.get("created_at"):
        return parse_time(previous.get("created_at")).isoformat()
    return (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()


def status_breakdown(issues: List[Dict[str, Any]]) -> Dict[str, int]:
    output: Dict[str, int] = {}
    for issue in issues:
        status = issue.get("status") or "Unknown"
        output[status] = output.get(status, 0) + 1
    return output


def serialize_run(record: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(record or {})
    data["issues"] = data.get("issues") or []
    data["summary"] = data.get("summary") or {}
    data["recipients"] = data.get("recipients") or []
    return data


def email_text(run: Dict[str, Any], key: str, link: str) -> str:
    changed_count = int(run.get("updated_count") or 0)
    new_count = int(run.get("new_count") or 0)
    total_count = int(run.get("total_count") or 0)
    changed = [issue for issue in run.get("issues", []) if issue.get("was_updated") or issue.get("is_new")]
    lines = [
        f"{key} project update",
        f"{changed_count} changed Jira tickets, {new_count} new tickets, {total_count} total tracked.",
        f"Window: since {jira_time(run.get('compare_since'))}",
        "",
        "Highlights:",
    ]
    for issue in changed[:8]:
        lines.append(f"- {issue.get('key')}: {issue.get('summary')} ({issue.get('status')})")
    if not changed:
        lines.append("- No issue changed in this automatic window.")
    lines.extend(["", f"Open live report: {link}"])
    return "\n".join(lines)


def email_html(run: Dict[str, Any], key: str, link: str, include_snapshot: bool) -> str:
    changed_count = int(run.get("updated_count") or 0)
    new_count = int(run.get("new_count") or 0)
    total_count = int(run.get("total_count") or 0)
    issues = run.get("issues", [])
    changed = [issue for issue in issues if issue.get("was_updated") or issue.get("is_new")]
    unchanged_count = max(0, len(issues) - len(changed))
    status_items = sorted(
        (run.get("summary") or {}).get("by_status", {}).items(),
        key=lambda item: int(item[1] or 0),
        reverse=True,
    )[:6]
    issue_rows = ""
    if changed:
        for issue in changed[:8]:
            badge = "New" if issue.get("is_new") else "Updated"
            issue_rows += f"""
            <tr>
              <td style="padding:14px 0;border-bottom:1px solid #e5eaf2;">
                <div style="font-size:12px;font-weight:800;color:#2f6fed;text-transform:uppercase;">{escape(str(issue.get('key') or ''))} · {badge}</div>
                <div style="margin-top:5px;font-size:15px;font-weight:800;color:#162033;line-height:1.35;">{escape(str(issue.get('summary') or ''))}</div>
                <div style="margin-top:5px;font-size:13px;color:#667085;">{escape(str(issue.get('status') or 'Unknown'))} · {escape(str(issue.get('assignee') or 'Unassigned'))} · updated {escape(format_email_time(issue.get('updated')))}</div>
              </td>
            </tr>
            """
    else:
        issue_rows = """
        <tr>
          <td style="padding:18px 0;color:#667085;border-bottom:1px solid #e5eaf2;">No issue changed in this automatic window. This is a clean status heartbeat.</td>
        </tr>
        """
    status_html = "".join(
        f"""<span style="display:inline-block;margin:0 6px 8px 0;padding:7px 10px;border-radius:999px;background:#edf3f8;color:#667085;font-size:12px;"><strong style="color:#162033;">{int(count or 0)}</strong> {escape(str(status))}</span>"""
        for status, count in status_items
    )
    snapshot_html = (
        '<tr><td style="padding:16px 0 0;"><img src="cid:app_snapshot" alt="Project update preview" style="width:100%;height:auto;border:1px solid #e5eaf2;border-radius:12px;"></td></tr>'
        if include_snapshot else ""
    )
    return f"""
    <div style="margin:0;padding:24px;background:#f3f6fb;font-family:Inter,Arial,sans-serif;color:#162033;">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:760px;margin:0 auto;background:#ffffff;border:1px solid #d8e0ea;border-radius:16px;overflow:hidden;">
        <tr>
          <td style="padding:20px 24px;border-bottom:1px solid #e5eaf2;background:#f7faff;">
            <div style="font-size:12px;font-weight:900;color:#2f6fed;text-transform:uppercase;">Project brief</div>
            <div style="margin-top:6px;font-size:24px;font-weight:900;color:#162033;">{escape(key)} Jira update</div>
            <div style="margin-top:4px;font-size:14px;color:#667085;">Prepared {escape(format_email_time(run.get('created_at')))} · since {escape(jira_time(run.get('compare_since')))}</div>
          </td>
        </tr>
        <tr>
          <td style="padding:24px;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
              <tr>
                <td style="vertical-align:top;">
                  <div style="font-size:13px;color:#667085;">Stakeholder summary</div>
                  <div style="margin-top:8px;font-size:16px;line-height:1.55;color:#162033;">{escape(key)} has <strong>{changed_count}</strong> ticket updates, including <strong>{new_count}</strong> new items.</div>
                </td>
                <td width="118" style="vertical-align:top;text-align:center;">
                  <div style="background:#162033;color:#ffffff;border-radius:14px;padding:18px 10px;">
                    <div style="font-size:34px;font-weight:900;line-height:1;">{changed_count}</div>
                    <div style="font-size:12px;color:#c8d3df;">changed</div>
                  </div>
                </td>
              </tr>
            </table>
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:18px;">
              <tr>
                <td style="padding:13px;border:1px solid #e5eaf2;border-radius:12px;"><strong style="font-size:22px;">{total_count}</strong><br><span style="font-size:12px;color:#667085;">Total tickets</span></td>
                <td width="12"></td>
                <td style="padding:13px;border:1px solid #e5eaf2;border-radius:12px;"><strong style="font-size:22px;">{new_count}</strong><br><span style="font-size:12px;color:#667085;">New tickets</span></td>
                <td width="12"></td>
                <td style="padding:13px;border:1px solid #e5eaf2;border-radius:12px;"><strong style="font-size:22px;">{unchanged_count}</strong><br><span style="font-size:12px;color:#667085;">Unchanged</span></td>
              </tr>
            </table>
            <div style="margin-top:24px;font-size:16px;font-weight:900;">Highlights</div>
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">{issue_rows}</table>
            <div style="margin-top:22px;font-size:16px;font-weight:900;">Status mix</div>
            <div style="margin-top:10px;">{status_html or '<span style="color:#667085;">No status data available.</span>'}</div>
            {f'<div style="margin-top:24px;"><a href="{escape(link, quote=True)}" style="display:inline-block;padding:11px 16px;border-radius:10px;background:#2f6fed;color:#ffffff;text-decoration:none;font-weight:900;">Open live report</a></div>'}
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">{snapshot_html}</table>
          </td>
        </tr>
      </table>
    </div>
    """


def format_email_time(value: str) -> str:
    return parse_time(value).strftime("%b %d, %H:%M")


@router.get("/runs")
def list_runs():
    return {"items": [serialize_run(item) for item in runs.list(sort="-created_at", perPage=30)]}


@router.get("/runs/{run_id}")
def get_run(run_id: str):
    return serialize_run(runs.get(run_id))


@router.get("/email-preferences/{raw_key}")
def get_email_preference(raw_key: str):
    key = jira_key(raw_key)
    return {"jira_key": key, "recipients": saved_recipients(key)}


@router.post("/generate")
def generate_project_update(req: ProjectUpdateRequest):
    key = jira_key(req.jira or req.epic_key)
    if not key:
        raise HTTPException(status_code=400, detail="Jira epic is required")

    since_iso = compare_since_for_request(req)
    since = parse_time(since_iso)
    jql = epic_jql(key)
    fields = ["summary", "status", "assignee", "updated", "created", "priority", "issuetype"]

    try:
        raw_issues = _integration("jira").search_all(jql, limit=250, fields=fields)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Jira search failed: {exc}") from exc

    issues = [summarize_issue(issue, since) for issue in raw_issues]
    changed = [issue for issue in issues if issue["was_updated"] or issue["is_new"]]
    recipients = req.recipients or saved_recipients(key)
    save_recipients(key, recipients)
    run = runs.create(
        {
            "epic_key": key,
            "compare_since": since_iso,
            "created_at": now_iso(),
            "created_by": ctx.user_email or ctx.user or "hangar",
            "jql": jql,
            "recipients": recipients,
            "total_count": len(issues),
            "updated_count": len(changed),
            "new_count": len([issue for issue in changed if issue["is_new"]]),
            "email_sent": False,
            "issues": issues,
            "summary": {
                "by_status": status_breakdown(issues),
                "changed_keys": [issue["key"] for issue in changed],
            },
        }
    )

    return {"run": serialize_run(run)}


@router.post("/runs/{run_id}/send")
def send_project_update(run_id: str, req: SendEmailRequest):
    run = serialize_run(runs.get(run_id))
    key = jira_key(run.get("epic_key"))
    recipients = req.recipients or run.get("recipients") or saved_recipients(key)
    if not recipients:
        raise HTTPException(status_code=400, detail="Email recipients are required")

    save_recipients(key, recipients)
    changed_count = int(run.get("updated_count") or 0)
    subject = req.subject.strip() or f"{key}: {changed_count} Jira updates"
    route = f"/?run={run['id']}&snapshot=email"
    link = app_url(f"/?run={run['id']}")
    text = email_text(run, key, link)
    try:
        email_result = _email().send(
            to=recipients,
            subject=subject,
            text=text,
            html=email_html(run, key, link, include_snapshot=True),
            app_snapshots=[
                {
                    "cid": "app_snapshot",
                    "route": route,
                    "width": 980,
                    "height": 1280,
                    "quality": 92,
                    "wait_ms": 1200,
                    "full_page": True,
                }
            ],
        )
        run = runs.update(run_id, {"recipients": recipients, "email_sent": True, "email_result": email_result})
    except Exception as snapshot_exc:
        try:
            fallback_result = _email().send(
                to=recipients,
                subject=subject,
                text=text,
                html=email_html(run, key, link, include_snapshot=False),
            )
            email_result = {
                "snapshot_fallback": True,
                "snapshot_error": str(snapshot_exc),
                "fallback_email": fallback_result,
            }
            run = runs.update(run_id, {"recipients": recipients, "email_sent": True, "email_result": email_result})
        except Exception as exc:
            email_result = {"error": str(exc), "snapshot_error": str(snapshot_exc)}
            run = runs.update(run_id, {"recipients": recipients, "email_sent": False, "email_result": email_result})
            raise HTTPException(status_code=502, detail=f"Email send failed: {exc}") from exc

    return {"run": serialize_run(run)}


@router.post("/run")
async def run_project_update(req: ProjectUpdateRequest):
    return await generate_project_update(req)
