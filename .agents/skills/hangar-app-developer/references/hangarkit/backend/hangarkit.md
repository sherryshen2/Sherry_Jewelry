# Python backend hangarkit module

ID: `backend.hangarkit`
Category: `backend`

Request-aware Python helpers for app context, URLs, assets, cache, short links, and app-scoped table access.

## Import

`from hangarkit import app_url, api_url, asset_url, cache, ctx, short_url, table`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `ctx.app_id, ctx.app_slug, ctx.user, ctx.user_email, ctx.current_user, ctx.user_name, ctx.user_avatar_url, ctx.request_id, ctx.origin`
- `app_path(path), app_url(path), api_path(path), api_url(path)`
- `asset_path(filename), asset_url(filename, thumb=None, download=False)`
- `table(name).list(**params), page(**params), get(id), create(data), update(id, data), upsert(id, data), delete(id), create_many(records), delete_many(ids)`
- `cache.get(key), cache.has(key), cache.set(key, value, ttl=None), cache.delete(key), cache.remember(key, ttl, loader)`
- `short_url.generate(title, real_url, expire_days=30), short_url.generate_short_url(...), short_url.records(page=1, per_page=50), short_url.list_records(...)`

## Details

Use `backend/main.py` for secrets, privileged integrations, CPU-heavy work, and APIs that should not run in the browser.

Export either `router = APIRouter()` or `app = FastAPI()` / ASGI. The Hangar runner starts `uvicorn _hangarkit_runner:app`, injects `hangarkit.ctx`, enforces internal gateway token checks, and routes public calls through `{prefix}/apps/:slug/api/*`.

## Backend secrets

Store secrets in `settings.services.secrets.variables` as `{ key, value }` entries. Backend code reads them with `os.getenv("NAME")`; never expose them in frontend code, responses, or logs.

Saved secret changes apply automatically on the next backend request. Hangar detects the changed environment and starts a refreshed backend before forwarding that request. Users do not need to restart or publish. Secrets are shared by Preview and the published app; updating them does not publish draft code.

This is automatic backend replacement, not a live secret lookup on every `os.getenv` call. Already-running requests and background work retain their process's environment until that process stops. The first request after a change may wait for backend startup.

Hangar forwards request cancellation to the backend HTTP transport when the hosting adapter exposes an abort signal. A request already canceled before forwarding does not start upstream request work. Canceling that HTTP request does not guarantee that synchronous Python code or background jobs stop, and it does not roll back completed writes or external effects. A client timeout alone is not proof that a mutation did not happen.

## Route style

Current HangarKit table and SPFS helpers are synchronous. For endpoints using those helpers, default to plain `def` so FastAPI runs the blocking work in its thread pool and concurrent requests do not block the async event loop. Use `async def` only when the handler actually awaits non-blocking work, such as async streaming, WebSockets, an async HTTP client, request-body parsing, or asyncio primitives. Do not call synchronous HangarKit storage helpers directly from an `async def`; use a `def` handler or explicitly move that call to a thread worker.

Put app-specific Python dependencies in `backend/requirements.txt`. Hangar deploys merge those app requirements with platform runtime requirements and can infer known generated-app imports such as `httpx`, but generated and imported apps should still declare third-party packages they import so local development and deploy behavior match.

Docker backend deploys build app backends from `python:3.11-slim` by default for broad third-party package wheel compatibility. Maintainers can override the base image with `HANGARKIT_BACKEND_DOCKER_PYTHON_IMAGE`, for example `python:3.12-slim`, when the app dependencies support that Python version.

Provider-specific backend integrations are available under `hangarkit.integrations`. Use `backend.integrations` and related provider docs for ABTest, Jira, Confluence, Google, SPACE, SeaTalk, POP, PMP, and Wingman Chat helpers.

Backend code can read the same app-scoped records that frontend `$data` writes:

```python
from fastapi import APIRouter
from hangarkit import asset_url, table

router = APIRouter()

@router.get("/submissions/{submission_id}")
def submission(submission_id: str):
    record = table("submissions").get(submission_id)
    filename = record.get("attachment")
    return {
        "record": record,
        "asset_url": asset_url(filename) if filename else None,
    }
```

Table reads are paginated with a default of 100 and a legacy-compatible maximum `perPage` of 500; prefer pages of 100 or fewer for new apps, especially when records are large. `filter` supports one simple field comparison (`=`, `!=`, `>`, `>=`, `<`, or `<=`), and `sort` supports up to five comma-separated fields. Both are executed by the configured storage backend. Created and updated record data is limited to 10 MiB of JSON; use assets for large files or blobs.

`create_many(records)` inserts 1-100 JSON records atomically and returns `{"records": [...], "count": n}`. `delete_many(ids)` deletes 1-100 distinct IDs atomically and returns `{"deleted": [...]}`; missing IDs reject the batch. These operations use the current actor's table permissions and user scope. `upsert(id, data)` falls back to create only when update returns 404, not on other errors.

Persistent table data has a 5 GiB logical JSON quota per app by default. Platform admins can override it per app. Hangar allows up to 1% above the configured quota, capped at 16 MiB; growing writes return HTTP 413 when cached usage would exceed this allowance. Usage accounting is best-effort and persists in the background without serializing app writes. Concurrent writes, a cold cache, or unavailable counters can temporarily exceed the quota; counter failures do not fail record writes. Deleting records and updates that do not grow stored JSON remain allowed even above the limit. This limit is independent of backend memory and uploaded assets.

`table(name)` also works from backend-owned background tasks that run inside the Hangar backend process, such as a FastAPI startup task or a small in-process scheduler. Those calls are authorized with the app backend token as a system actor, so they do not need a browser user session. Keep background work lightweight and idempotent because the backend process may restart during deploys, local dev restarts, or platform recovery.

## Current user profile

`ctx.user` and `ctx.user_email` remain the stable ID and email shortcuts. For the same signed-in profile returned by frontend `auth.currentUser()`, use `ctx.current_user`. It is a dictionary with `id`, `email`, `name`, `wingman_user_id`, `role`, `inferred_role`, `avatar_url`, `feature_toggles`, `available_toggles`, `teams`, and `context`. `ctx.user_name` and `ctx.user_avatar_url` are convenient shortcuts.

```python
profile = ctx.current_user
return {
    "name": ctx.user_name,
    "avatar_url": ctx.user_avatar_url,
    "team_count": len(profile.get("teams", [])),
}
```

Backend-owned and public callback requests have no signed-in profile, so `ctx.current_user` is empty for those requests.

For records created by browser-side `$data` file uploads, file fields contain asset filenames. Use `asset_path()` or `asset_url()` when returning links to the frontend. Backend table CRUD sends JSON only; it does not upload Python file objects into file fields.

Physical asset bytes live on the owning Hangar VM's persistent disk, separately
from structured records. Asset URLs still go through Hangar authorization and
ALB routing; they are not public directory URLs. File reads do not require the
PocketBase process or MySQL blob storage.

There is no documented Python `asset_bytes()` helper. If backend code must inspect or transform raw upload bytes immediately, expose a FastAPI route that accepts `UploadFile`, process the stream in that route, and store any durable metadata or resulting asset filename in an app table.

Important for local development: live Hangar injects Python `hangarkit` into the backend runtime. For user-local testing, install the local SDK from `packages/hangarkit-python-sdk` and run `hangarkit dev --slug :slug`; app code should keep the same `from hangarkit import ...` imports used in live.
## Quick examples

- `notes = table("notes").list(sort="-created", perPage=20)`
- `filename = table("submissions").get(submission_id).get("attachment")`
- `return {"asset_url": asset_url(filename)}`
- `return {"home_url": app_url("/")}`
- `link = short_url.generate("Release notes", "https://example.com/release", expire_days=30)`

## Related capabilities

- `runtime.backend`
- `backend.cache`
- `backend.short_url`
- `backend.integrations`
- `frontend.hangarkit`
