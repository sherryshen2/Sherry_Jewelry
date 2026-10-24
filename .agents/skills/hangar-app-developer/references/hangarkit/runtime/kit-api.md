# Caller-only HangarKit API

ID: `runtime.kit_api`
Category: `runtime`

Discover public Python HangarKit methods and invoke supported methods through one caller-permission gateway, without deploying an app backend.

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `GET /api/external/hangar/kit/catalog?kit=google_drive&method=list_files&page=1&per_page=50`
- `POST /api/external/hangar/kit/call`
- `POST /api/external/hangar/apps/:app_id/kit/call`

## Details

Use this API to test supported public Python HangarKit methods directly from an
agent, curl, or another language. There are two operations, catalog and call,
not one HTTP endpoint per SDK function. No generated app or app backend is
needed for ordinary caller-linked integrations.
Use it from an agent or a trusted backend/test client. Never embed Wingman or
Connector tokens in generated frontend code, or use a builder's token to
authorize other app users. Running apps keep their normal HangarKit consent
and authentication flow.

## Authentication and caller permission

Use the public Hangar base, normally `https://wingman.shopee.io/hangar`, and send
`Authorization: Bearer $WINGMAN_TOKEN`. The gateway validates that specific
Wingman token and derives identity from it. Cookies, caller-supplied email
headers, app-owner settings, stored owner tokens, pasted app credentials, and
inherited server credentials never replace the caller's authority.

Legacy integrations use the caller's Wingman permission. Native Connector and
Relay kits require a caller Connector token in
`X-Connector-Token: Bearer $CONNECTOR_TOKEN`, or the caller's own existing
Connector grant in an authorized app context. A supplied Connector token must
allow `/api/proxy/user/me`; its verified email must match the Wingman caller.
Invalid or mismatched tokens fail without falling back to another account.
Linking, provider scopes, Relay readiness, and existing upstream safe-mode
rules still apply.

Reads and writes use the same call operation. There is no additional gateway
confirmation flag or read-only mode. Uploads, deletes, sends, and other writes
are real operations, not simulated tests. For catalog-backed SDK `call()`
methods, explicit gateway invocation supplies the SDK's normal confirmation
opt-in by default; it never overrides an upstream permission or safe-mode
denial. Existing SDK `preview` options remain available where supported.
Caller permission does not expand a calling agent's task authorization; use
fixtures for destructive verification unless the user requested the real action.

## Discover methods

```bash
curl -sS -G "$HANGAR_BASE_URL/api/external/hangar/kit/catalog" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  --data-urlencode 'kit=google_drive' \
  --data-urlencode 'method=upload_file'
```

Optional filters are `kit`, `method`, and `q`; results use `page` and `per_page`
(default 50, maximum 100). Each method includes its signature, parameter names,
required inputs, defaults, `callable`, `requires_app`, and any
`unavailable_reason`. The catalog is derived from the shipped SDK's public
exports and client signatures, not request-supplied module imports.

Catalog discovery describes methods and requirements; it does not prove that
the caller has linked a provider or can perform a particular operation.
Factories, credential-returning helpers, Python callbacks/objects, live Python
streams, local filesystem helpers, and process-local continuation workflows
are not made remotely executable. The catalog explains these restrictions.
App-provided SeaTalk bot credentials, the platform-owned InfraBot kit,
app/platform LLM credentials, platform mail senders, and platform short-link
credentials are not borrowed for caller-only testing. Use caller-linked kits
such as `google_mail` where appropriate.

## Invoke a method

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/kit/call" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"kit":"google_drive","method":"list_files","params":{"page_size":20}}'
```

The JSON object accepts `kit`, `method`, `params`, and optional `output`
(`json` by default, or `binary`). `params` supplies SDK keyword arguments; the
dispatcher binds the actual SDK signature before execution. Only registered
public methods are accessible. Private attributes, arbitrary imports,
expressions, Python source, local paths, and owner/app auth overrides are not
accepted.

Successful JSON calls return:

```json
{
  "kit": "google_drive",
  "method": "list_files",
  "permission_mode": "caller",
  "request_id": "...",
  "result": {"files": [], "nextPageToken": "..."}
}
```

Credential fields and caller tokens are redacted; ordinary pagination tokens
remain usable. Errors preserve appropriate HTTP statuses and return `error`,
`permission_mode`, and `request_id`, without a Python traceback or credentials.
Inputs and uploaded bodies are omitted from gateway audit summaries.

## Binary uploads and results

For file input, send `multipart/form-data` containing one JSON `call` field and
named file parts. Reference a file part with `{"$file":"part_name"}` inside
`params`, including nested parameter objects. Filenames are labels, never
server filesystem paths.

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/kit/call" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  -F 'call={"kit":"google_drive","method":"upload_file","params":{"name":"report.pdf","content":{"$file":"document"},"mime_type":"application/pdf","parent_id":"selected-folder-id"}}' \
  -F 'document=@/absolute/path/report.pdf;type=application/pdf'
```

Replace folder IDs and file paths with actual values before executing. Do not
run placeholders. Use `list_files()` to browse folders and select an accessible
destination; folder selection does not grant write permission.

JSON output encodes Python bytes as `{"$binary":"base64..."}`. For file-returning
methods, request `"output":"binary"` to return the raw bytes, including methods
returning a `content` byte field or a document conversion result.

## App-bound methods

Tables, app cache, assets, document conversion, app email records, app URLs, and
Wingman Chat need an existing app context. Call the same dispatcher at
`/api/external/hangar/apps/:app_id/kit/call`; this app-scoped URL lets the
gateway route to the owning VM. App edit permission is required, as with the
external app-management API. A body `app_id`, if provided, must match the URL;
do not pass it to the unscoped call URL.

For table operations, use kit `table`, a normal SDK table method such as
`page`, `get`, `create`, `update`, or `delete`, and put the table name in
`params.name`. Calls use the authenticated caller as an authenticated actor,
not a system actor or the app owner. Existing table permissions and user scope
remain enforced. Writes target the app's live records; they are not a mock
database or a preview-only sandbox. No app source code is executed.

## Limits and runtime setup

- JSON input: 1 MiB. File parts: 20 MiB total, at most 10 parts; allow up to
  1 MiB additional multipart/descriptor overhead.
- Upstream bodies and returned JSON/binary results are bounded to 20 MiB.
  A base64 JSON result can exceed the JSON budget before its raw bytes do;
  use binary output for large file results.
- Request-body reading, SDK execution, and response transfer each have a
  30-second deadline.
  Execution permits at most 32 SDK HTTP requests.
  There is no automatic gateway retry, including for writes.
- Admission is bounded to four workers per Node process and two per caller
  per process, covering input parsing, execution, and response consumption,
  with no waiting queue.
  Busy requests return 429 and Retry-After before their bodies are read.
  These are per-process limits, not a globally coordinated user quota.
- Failed, timed-out, or cancelled calls do not prove that a write was rolled
  back. Check the result in the provider before retrying.
- Linux executors also enforce 512 MiB virtual address-space and 30 CPU-second
  ceilings. Other development OSes retain the gateway byte, concurrency, and
  deadline limits; do not treat a passing development call as a load test.

The executor loads only platform-owned SDK code. It cannot load app source or
request-supplied Python. Caller credentials remain in the gateway; worker
HTTP is brokered through caller-bound routing. Each invocation has isolated,
disposable scratch and no inherited account secrets.

Docker builds install the platform interpreter and dependencies. For other
deployments, run `npm run kit:setup` (optionally
`npm run kit:setup -- python3.11`). The default interpreter is
`.hangarkit/runtime/kit-venv/bin/python`; configure an absolute
`HANGARKIT_KIT_PYTHON` path to use another trusted platform environment. Never
select an app's environment or install packages based on a call's input.
Missing runtime dependencies return 503 rather than using another account,
an app backend, or a desktop login.
## Related capabilities

- `backend.integrations`
- `backend.integration.google_drive`
- `workflow.app_performance`
