# Developing a Hangar App

## Files and Runtime

| Path | Purpose |
| --- | --- |
| `frontend/src/App.svelte` | Main frontend |
| `frontend/src/components/` | Frontend components |
| `backend/main.py` | Python/FastAPI entry |
| `backend/requirements.txt` | Backend dependencies |
| `design/design.md` | Durable app requirements and design decisions |

Read the existing app before editing. Keep `design/design.md` current with
durable decisions, not credentials, turn transcripts, or temporary status.

New frontend code uses Svelte 5 runes and event attributes such as `onclick`.
Keep browser-only work inside client lifecycle/effects or event handlers.
Checks and publishing compile for the browser; static template thumbnails still
server-render. Preserve working compatibility
syntax in existing code unless migration is part of the request.

Hangar supplies `$hangarkit`, `$data`, `$content`, and `$design` to the frontend
and `hangarkit` to Python. Do not replace them because a plain local editor
cannot resolve them. Use app-scoped helpers instead of hardcoding app IDs,
another app's routes, or a custom domain. Runtime URLs use `/apps/:slug` after
the deployment's optional prefix; use URLs returned by the API.

Export `router = APIRouter()` or an ASGI `app` from `backend/main.py`.
List third-party imports, including `fastapi` and `uvicorn`, in backend
requirements. Use synchronous routes for synchronous helpers, or offload
blocking work when using async handlers.

For substantial backends, `backend/main.py` can compose `backend/routers/`
and `backend/services/`. Keep a trivial backend simple and preserve an existing
sensible structure. For a substantial change to an existing monolithic
backend, ask the user before reorganizing unrelated code. Respect a no.

## Data and Integrations

- Match `$content` references and editable CSS variables with top-level
  Content and Design metadata. Read and merge existing arrays before patching.
- Table definition changes are separate from record writes. Do not replace
  or delete records to fix code. Use the documented app-scoped data helpers.
- Use asset helpers for stored files rather than temporary local file paths.
- Keep integration credentials in Hangar settings/Secrets, never frontend
  code. Read the named provider's capability page before implementing calls.
- Relay-backed integrations default to the current app user's account.
  Preserve explicit choices. Only Order Admin supports explicitly requested
  owner mode among the Relay providers; consult its reference before choosing it.
- Owner-only Connector consent must be completed by the actual app owner.
  Report outstanding authorization accurately; do not borrow an editor's
  account or claim that consent proves the provider call works.

## Performance

Read [limits and efficiency](hangarkit/workflow/app-performance.md) before
adding data access, integrations, polling, or background work, and for new
apps or performance fixes. Node/storage capacity is shared across apps;
Python process isolation does not make large table reads cheap. Use small
pages, bounded concurrency, and asset references. Record durable paging,
payload, refresh, and job budgets in `design/design.md` when relevant.
Review payloads and representative behavior; compilation is not a load test.

## Sync and Verify

Use the bundled CLI for revision-checked source sync. Inspect `diff` before
`pull` or `push`; do not force over conflicts. `diff` and `push` compare local
UTF-8 byte hashes against the manifest without downloading all source.
`push --apply` stages only changed files in resumable byte batches: at most
128 file chunks, 256 KiB total decoded raw bytes, and 512 KiB JSON per request.
Small files share a batch; large files can use the remaining batch budget.
It checks byte progress for every attempted chunk,
then verifies and commits them in one revision-checked write. The CLI verifies
the resulting manifest. Re-run the same push after interruption to resume
offsets; a revision conflict stops rather than overwriting someone else's work.
An ambiguous batch retries the identical session/offsets/bytes; partially
accepted batches are safe to resubmit because equal chunks are idempotent.
Metadata and table commands are separate operations. Missing local files do
not authorize remote deletion; only explicit `--delete` removes remote-only
files, including files outside any selected source directories.

Use a dedicated app folder. Collection keeps the existing text-file layout,
excluding `data/`, `hangar-app.json`, `.git`, `.hangar`, `.hangarkit`,
`node_modules`, `__pycache__`, `.codex`, `.openai`, `.local`, `.venv`, `venv`,
`dev`, `.env*`, `.user-token`, and symlinks. For a game/repository folder with
Node tooling, pass `--source-dir frontend/src --source-dir backend --source-dir
design` to `diff`, `push`, and `release`. Paths remain app-relative; only these
trees are collected. Select other source trees explicitly if the app needs them.
Do not put secrets in source even when a filename is not excluded.

Run `check` after frontend changes and exercise the changed behavior when a
preview or local test environment is available. A frontend compile pass
does not prove client interaction or an integration works. Clearly distinguish
checks actually run from checks blocked by missing credentials or a browser.

Saving source creates a draft; publishing is a separate explicit action.
Hosted editing sessions finish before the user publishes. Local developers
may use `publish --apply` when publishing was requested. Do not silently change
sharing as part of either action.

For a requested local release, run `release --app "$APP_ID" --dir "$APP_DIR"
--apply`. It stages source, syncs local `data/*.json` definitions only, rechecks
the draft hash, checks that exact source, waits for async publish, and verifies
the runtime shell and `/api/_hangarkit/health` with fresh authentication.
`deploy` is an alias for this workflow. It does not upload `hangar-app.json`,
change app identity/sharing, delete tables, or insert/replace/delete records.
On an ambiguous definition-write response it reads `?schema_only=true` before
retrying; an already-saved definition is not rewritten, and concurrent changes
stop the release. Definition retries are bounded and never inspect records.
Check and publish reuse the server's compiled artifact for unchanged source.
No-op source sync uses the manifest's full `source_hash` without an upload.

The default publication wait is 900 seconds, configurable up to 3600 with
`--wait-timeout`; each HTTP request is also bounded. Progress goes to stderr,
and `--json` leaves one final result on stdout. After interruption, re-run the
same release command with the same app, host, directory, and source. Non-secret
`.hangar/release.json` preserves the idempotency key, job ID, and source hash.
Recovery polls an existing job or retries the exact original key, not a new
version. Changed source is blocked while a prior job is unresolved. Inspect the
job's terminal outcome before deliberately removing old release state.
Runtime verification failure retains the ready job so re-running verifies
again without republishing. Older servers missing staged/hash-pinned APIs fail
clearly; there is no full-source or synchronous publish fallback.

Published runtime routes require Hangar browser-session authentication;
an external API bearer token alone does not authenticate a browser page.
Follow [runtime verification](external-api.md#runtime-verification) to exchange
it for a session. Test in a fresh page and exercise the changed controls.
If runtime data is correct but the UI is stale, check client errors and cached
bundles before changing records.

Preview code and test records are separate from the published app. Table
definitions, assets, credentials, and external effects are shared; tests can
still have real external effects. Publishing or rolling back code does not
restore those resources.
