# Google Mail integration

ID: `backend.integration.google_mail`
Category: `backend`

Search, inspect, draft, send, label, archive, trash, and read Gmail attachments from backend code.

## Import

`from hangarkit.integrations import google_mail`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `google_mail.attachment(content, filename, content_type="application/octet-stream")`
- `google_mail.search_messages(query=None, mailbox=None, start_date=None, end_date=None, max_results=20, ...), search_inbox(query=None, **kwargs), search_sent(query=None, **kwargs), search_drafts(query=None, **kwargs)`
- `google_mail.get_message(...), get_message_detail(...), get_thread(...)`
- `google_mail.list_drafts(query=None, max_results=20, ...), get_draft(draft_id, user_id="me", format="full"), create_draft(to=None, subject=None, body_text=None, body_html=None, attachments=None, ...), update_draft(draft_id, ..., attachments=None), send_draft(draft_id, user_id="me")`
- `google_mail.send_message(to=None, subject=None, body_text=None, body_html=None, cc=None, bcc=None, thread_id=None, headers=None, raw=None, attachments=None, user_id="me")`
- `google_mail.modify_message(...), archive_message(...), mark_read(...), mark_unread(...), trash_message(...), untrash_message(...)`
- `google_mail.list_labels(...), get_attachment(...)`
- `google_mail.create_raw_message(...), message_summary(...), message_detail(...)`
- `google_mail.request(method, path, **kwargs)`

## Details

Use this module for Gmail workflows that belong in backend code, especially draft/send/search operations and attachment reads.

Be explicit about side effects. Searching and reading are safe; draft creation, sending, trashing, and label changes modify the user's mailbox through the configured integration auth.

### Compose and mailbox workflow

Use `to`, `subject`, and either `body_text` or `body_html` to let HangarKit construct the Gmail raw message. Use `google_mail.attachment()` for every binary attachment; it accepts bytes and returns the same canonical `data`, `content_type`, and `filename` object shape as `hangarkit.email.attachment()`. Pass those objects through `attachments=[...]` when creating or sending a message. Set `raw` only when the app already has a correctly encoded Gmail MIME payload; it cannot be combined with `attachments`.

```python
from hangarkit.integrations import google_mail

draft = google_mail.create_draft(
    to=["team@example.com"],
    subject="Status update",
    body_text="The deployment is complete.",
)
google_mail.send_draft(draft["id"])
```

```python
from hangarkit.integrations import google_mail

result = google_mail.send_message(
    to=["team@example.com"],
    subject="Weekly report",
    body_text="The report is attached.",
    attachments=[google_mail.attachment(
        report_bytes,
        filename="weekly-report.pdf",
        content_type="application/pdf",
    )],
)
```

`send_message()` sends immediately, while `create_draft()` does not. `get_message(message_id, ...)`, `get_thread(thread_id, ...)`, and `get_attachment(message_id, attachment_id, ...)` require their respective Gmail IDs. Use `modify_message(message_id, add_label_ids=None, remove_label_ids=None)` for label updates; archive, read/unread, trash, and untrash are explicit convenience methods with mailbox side effects.
## Quick examples

- `results = google_mail.search_messages("from:alice@example.com newer_than:7d")`
- `draft = google_mail.create_draft(to=["team@example.com"], subject="Update", body_text="Hello")`

## Related capabilities

- `backend.integrations`
