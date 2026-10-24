# Email

ID: `backend.email`
Category: `backend`

Send email from backend code through Hangar's audited, quota-limited email gateway.

## Import

`from hangarkit import email`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `email.attachment(content, filename, content_type="application/octet-stream")`
- `email.send(to=[...], subject="...", text="...", html="...", cc=[...], bcc=[...], attachments=[...])`
- `email.send_app_snapshot(to=[...], subject="...", route="/dashboard", message="...")`
- `email.send_email(...)`
- `email.records(page=1, per_page=50)`

## Details

Use this helper when an app backend needs to send email. Hangar routes every request through `{prefix}/apps/:slug/email/send`, verifies the backend token, enforces the app's daily quota, writes an email event for admin review, and emits runtime audit logs.

The platform admin configures the downstream email provider host, snapshot public base URL, and default quotas in Admin > Email. Per-app daily quotas are also managed there.

Email bodies are forwarded to the configured provider but are not copied into the admin event table; the event stores subject, recipients, actor, status, quota usage, and provider result or error.

```python
from fastapi import APIRouter
from hangarkit import email

router = APIRouter()

@router.post("/notify")
async def notify():
    result = email.send(
        to=["team@example.com"],
        subject="Hangar notification",
        text="The report is ready.",
    )
    return {"ok": True, "email": result}
```

Use `email.attachment()` for every binary attachment. It accepts bytes and returns Hangar's canonical attachment object: base64 `data`, `content_type`, and recipient-visible `filename`. Hangar validates that object and maps it to the configured provider; app code must not use provider-specific fields such as `cid`.

To convert an uploaded office file and email the resulting PDF, combine `documents.convert_upload()` with `email.attachment()`:

```python
from fastapi import APIRouter, UploadFile
from hangarkit import documents, email

router = APIRouter()

@router.post("/convert-and-email")
async def convert_and_email(upload: UploadFile):
    pdf = await documents.convert_upload(upload)
    result = email.send(
        to=["team@example.com"],
        subject="Converted document",
        text="The PDF is attached.",
        attachments=[email.attachment(
            pdf.content,
            filename=pdf.filename,
            content_type=pdf.content_type,
        )],
    )
    return {"ok": True, "email": result}
```

Use `email.send_app_snapshot()` when the email should contain the app itself. Hangar mints a short-lived same-app render token, asks the configured provider to capture the route, and embeds the screenshot as an inline image. The render token does not require a user login, is scoped to the current app, expires quickly, and only grants read access for the rendered frontend, assets, data, and cache reads needed by the page.

For app snapshots, the provider's browser must be able to reach the generated app URL. If Hangar is running behind a tunnel, staging host, or another public entry point, set Admin > Email > Snapshot public base URL to that reachable Hangar base, such as `https://wingman.example.com` or `https://wingman.example.com/hangar`. When it is blank, Hangar falls back to the current request origin.

```python
from fastapi import APIRouter
from hangarkit import email

router = APIRouter()

@router.post("/send-dashboard")
async def send_dashboard():
    result = email.send_app_snapshot(
        to=["team@example.com"],
        subject="Daily dashboard",
        route="/dashboard",
        message="Current dashboard snapshot attached.",
        width=1280,
        height=900,
        wait_ms=2000,
    )
    return {"ok": True, "email": result}
```
## Related capabilities

- `backend.hangarkit`
- `backend.documents`
- `runtime.routing`
