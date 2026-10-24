# Google Drive integration

ID: `backend.integration.google_drive`
Category: `backend`

List, search, upload, replace content, manage metadata and folders, export, and share Google Drive files.

## Import

`from hangarkit.integrations import google_drive`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `google_drive.list_files(q=None, page_size=100, ...), search_files(query, **kwargs), get_file(file_id, fields=..., supports_all_drives=True)`
- `google_drive.create_file_metadata(name, mime_type=None, parent_id=None, parents=None, fields=...), create_folder(name, parent_id=None, parents=None, fields=...)`
- `google_drive.upload_file(name, content, mime_type="application/octet-stream", parent_id=None, parents=None, metadata=None, fields=..., supports_all_drives=True, timeout=30)`
- `google_drive.update_file_content(file_id, content, mime_type="application/octet-stream", metadata=None, fields=..., supports_all_drives=True, timeout=30)`
- `google_drive.update_file(file_id, metadata, ...), copy_file(file_id, name=None, parent_id=None, parents=None, ...), delete_file(file_id, supports_all_drives=True)`
- `google_drive.export_file(...), export_file_bytes(...)`
- `google_drive.download_file(...), download_text_file(...)`
- `google_drive.view_url(...), preview_url(...), embed_url(...)`
- `google_drive.list_permissions(...), create_permission(...)`
- `google_drive.request(method, path, **kwargs), request_bytes(method, path, **kwargs)`

## Details

Use this module for Google Drive API workflows from backend code. The helpers cover content uploads and replacement, metadata, folders, permissions, export, copy, update, delete, and search/list operations through Hangar integration auth.

Prefer Google Drive for user-managed documents, uploads, and generated files.
For new workflows where each user should own their files, explicitly configure
`settings.integrations.google_drive` with `{"auth_mode": "user"}`; the default
owner-account mode does not give each user ownership. Preserve existing explicit
shared-account choices. Store Drive file IDs, links, and compact metadata in
Hangar rather than copying file contents into records or source. Keep
application-owned static assets in Hangar, and never widen file sharing or move
existing assets to Drive automatically.

Use `download_file()` for binary Drive files such as uploaded HTML, PDFs, images, and archives. Use `download_text_file()` for text-like Drive files such as HTML source when the app needs to inspect or sanitize text before rendering. Use `export_file_bytes()` for Google-native files, such as exporting Google Slides to `application/pdf`.

Binary helpers return a dict with `content` bytes, `content_type`, `content_disposition`, `headers`, and `status`. A backend route can pass that through with FastAPI:

```python
from fastapi import Response
from hangarkit.integrations import google_drive

@router.get("/documents/{file_id}/pdf")
def document_pdf(file_id: str):
    result = google_drive.export_file_bytes(file_id, "application/pdf")
    return Response(content=result["content"], media_type=result["content_type"])
```

Use `preview_url()` or `embed_url()` when the app should embed Google’s own viewer in an iframe and let Google enforce the viewer’s document access.

### File and sharing workflow

`file_id` is required for file-specific helpers. `create_file_metadata()` and
`update_file()` still operate on metadata only. Use `upload_file()` for a new
file with content, or `update_file_content()` to replace an existing file's bytes.

```python
from hangarkit.integrations import google_drive

folder = google_drive.create_folder("Project Notes")
file = google_drive.create_file_metadata("brief.txt", mime_type="text/plain", parent_id=folder["id"])
google_drive.update_file(file["id"], {"description": "Current project brief"})
google_drive.create_permission(file["id"], role="reader", permission_type="user", email_address="team@example.com")
```

`create_permission(file_id, role, permission_type, email_address=None, domain=None, ...)` requires a role and permission type. Use `download_file()` for binary content, `download_text_file()` for decoded text, and `export_file_bytes(file_id, mime_type)` for Google-native files. `delete_file()` permanently deletes the Drive file, so only call it after an explicit user decision.

### Upload and content replacement

```python
from hangarkit.integrations import google_drive

file = google_drive.upload_file(
    "brief.txt",
    "Current project brief",
    mime_type="text/plain",
    parent_id=folder_id,
    metadata={"description": "Project notes"},
)
google_drive.update_file_content(
    file["id"],
    b"Revised project brief",
    mime_type="text/plain",
    metadata={"name": "brief-v2.txt"},
)
```

Both helpers accept `bytes`, `bytearray`, `memoryview`, or text encoded as UTF-8.
They do not accept file paths or open file objects. File content is bounded to
20 MiB per call and JSON metadata to 64 KiB; oversize input fails before sending.
These are bounded, single-request helpers, not streaming or resumable uploads.
Larger files require a separate resumable workflow; do not split a file into
ordinary upload calls, which would create multiple files or replace its content.
The 20 MiB guard counts raw file bytes, not the multipart envelope or metadata,
and is a HangarKit safety ceiling rather than Google's maximum file size.
Prefer smaller transfers; larger single requests still buffer their content
and remain subject to Hangar and Connector timeouts.

Hangar's public app API responses have a separate 20 MiB limit through the ALB,
including binary downloads and streamed responses from `/apps/:slug/api/...`.
An upload returning compact file metadata does not return the uploaded bytes.
For viewing and downloading large user-managed files, prefer Google's own
authorized viewer/download flow where appropriate; a Drive link does not grant
access by itself. Do not assume storing a file in Drive allows a larger
single-response download through a Hangar app API.

`upload_file()` sends a `multipart/related` request with JSON metadata followed
by unchanged file bytes. The required `name` sets the file's name; explicit
`parent_id`/`parents` override parents in `metadata`. Other metadata is preserved
without mutating the caller's dict. `mime_type` describes the uploaded bytes;
an optional `metadata["mimeType"]` can request a supported Google-native import.

`update_file_content()` uses a media-only PATCH when `metadata` is omitted, or
multipart PATCH when a metadata dict is supplied. It replaces content; it is not
an append operation. Both helpers return Google's JSON file metadata, selected
by `fields`, and support `supports_all_drives=True` by default.

Uploads use the same configured current-user, app-owner, or supplied OAuth-token
auth as other Drive helpers. Account-backed calls require Connector's Drive
upload-path support. The grant must allow POST or PATCH and `/upload/drive/...`;
a read-only or metadata-path-only grant is insufficient. Appropriate Google
write scopes and explicit safe-mode policy approval are still required. Do not
request broad Google access or disable safe mode just to bypass an upload denial.

The helpers preserve upstream errors and never retry writes automatically. A
timeout or lost response can have an unknown outcome; check the destination
before retrying to avoid duplicate files. `timeout` controls the Python request;
Hangar and Connector still enforce their own timeouts and body-size limits.

Drive helper methods route relative paths through the generic Google connector with the `/drive` API prefix, matching Google Drive's canonical REST base `https://www.googleapis.com/drive`. For raw calls, prefer paths such as `/v3/files` or absolute URLs such as `https://www.googleapis.com/drive/v3/files`.

Upload helpers use the canonical absolute upload URL
`https://www.googleapis.com/upload/drive/v3/files` (with `/file_id` for content
replacement). Raw upload calls must also use this absolute URL: a relative
`/upload/...` would incorrectly append it beneath the normal `/drive` base.
## Quick examples

- `files = google_drive.search_files("mimeType = 'application/pdf'")`
- `folder = google_drive.create_folder("Project Notes")`
- `file = google_drive.upload_file("brief.txt", "Current project brief", mime_type="text/plain")`
- `pdf = google_drive.export_file_bytes(presentation_id, "application/pdf")`

## Related capabilities

- `backend.integrations`
- `backend.integration.google`
