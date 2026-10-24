from importlib import import_module
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from hangarkit import app_url, ctx

router = APIRouter()


class ShareDraftRequest(BaseModel):
    kind: str = "poll"
    poll: dict = Field(default_factory=dict)
    email: Optional[str] = ""
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


@router.post("/share-draft")
def share_draft(req: ShareDraftRequest):
    poll = req.poll or {}
    question = poll.get("question") or "Poll"
    email = (req.email or "").strip()
    link = req.link or app_url(f"/?poll={poll.get('slug') or poll.get('id') or ''}")
    subject = f"Vote: {question}"
    body = "\n".join(
        [
            f"Please vote in this poll: {question}",
            "",
            poll.get("description") or "",
            "",
            link,
        ]
    ).strip()
    mailto = f"mailto:{email}?subject={subject}&body={body}" if email else f"mailto:?subject={subject}&body={body}"
    gmail = _google_mail()
    if gmail and email:
        try:
            if hasattr(gmail, "send_message"):
                result = gmail.send_message(to=[email], subject=subject, body_text=body)
                return {"ok": True, "message": f"Poll email sent to {email}.", "result": result}
        except Exception as exc:
            return {
                "ok": False,
                "message": f"Email connector is not ready, but a draft link was prepared: {exc}",
                "mailto": mailto,
            }
    return {
        "ok": True,
        "message": "Poll email draft prepared. Copy the vote link or open the mailto draft.",
        "mailto": mailto,
        "subject": subject,
        "body": body,
    }
