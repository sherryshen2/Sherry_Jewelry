from importlib import import_module
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from hangarkit import app_url, ctx

router = APIRouter()


class InviteRequest(BaseModel):
    event: dict = Field(default_factory=dict)
    invitees: List[str] = Field(default_factory=list)
    link: str = ""


def _google_mail():
    try:
        integrations = import_module("hangarkit.integrations")
        return getattr(integrations, "google_mail")
    except Exception:
        return None


@router.get("/health")
def health():
    return {"status": "ok", "app": ctx.app_slug, "user": ctx.user_email}


@router.post("/send-invites")
def send_invites(req: InviteRequest):
    event = req.event or {}
    name = event.get("name") or "Event"
    invitees = [item.strip() for item in req.invitees if item and item.strip()]
    link = req.link or app_url(f"/?event={event.get('slug') or event.get('id') or ''}")
    subject = f"RSVP: {name}"
    body = "\n".join(
        [
            f"You're invited to {name}.",
            "",
            f"Date: {event.get('date') or 'TBD'}",
            f"Location: {event.get('location') or 'TBD'}",
            "",
            "Please RSVP here:",
            link,
        ]
    )
    mailto = f"mailto:{','.join(invitees)}?subject={subject}&body={body}"
    gmail = _google_mail()
    if gmail and invitees:
        try:
            if hasattr(gmail, "send_message"):
                result = gmail.send_message(to=invitees, subject=subject, body_text=body)
                return {"ok": True, "message": f"Invites sent to {len(invitees)} recipient(s).", "result": result}
        except Exception as exc:
            return {
                "ok": False,
                "message": f"Email connector is not ready, but a draft link was prepared: {exc}",
                "mailto": mailto,
            }
    return {
        "ok": True,
        "message": "Invite draft prepared. Copy the RSVP link or open the mailto draft.",
        "mailto": mailto,
        "subject": subject,
        "body": body,
    }
