# Relay portal integrations

ID: `connector_integration.relay_portals`
Category: `connector_integration`

Discover and call cataloged Relay portal operations with provider-scoped access and recovery.

## Import

`from hangarkit.integrations import order_admin, promotion_admin, cmt_admin, product_label_admin, ssc_ops, user_admin, listing_admin, bd_centre, tws, datasuite, seatalk_open, skyline, traffic_suite, cs_portal, dms_cs_portal, seller_sop, shopeefood_admin, noti_admin, chat_admin, listing_qc_admin, soup, leave_portal, mp_ai_dod, google_sites`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `provider.call(operation_id, *, env=None, region=None, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`
- `provider.request(method, path, *, env=None, region=None, params=None, json=None, data=None, headers=None, timeout=30, auth_mode=None, full_response=False)`
- `provider.get(path, **kwargs)`
- `provider.post(path, **kwargs)`
- `provider.put(path, **kwargs)`
- `provider.patch(path, **kwargs)`
- `provider.delete(path, **kwargs)`

## Details

Read `connector_integration.relay` first. Connector checks the app-specific permission and carries an approved request. Browser Relay is a background helper on the user's paired computer that can refresh the website session **when needed**. An existing session may work while Relay is offline. A Connector grant does not prove website access; a browser sign-in does not prove a business API will work.

Each provider below is a **separate Craft integration**, not a generic Relay integration. The 23 providers other than Order Admin use the **current app user's** Connector grant and website access; they do not support app-owner mode, service credentials, or unattended system/cron calls. Order Admin also supports explicit owner mode and `ensure_access`. All 24 have catalog-backed `call` and raw `request`. Google Sites is the special browser-executed job service, not a cookie-cached portal proxy. Read the provider page before choosing an API or target:

All 24 Relay providers default to **App User** mode (`auth_mode: "user"`) in Craft, server defaults, and template setup. Preserve the per-user default when building apps. The legacy owner-token migration does not change Relay integrations, and existing explicit auth choices remain unchanged. Only choose Order Admin owner mode when the user explicitly requests shared owner-account access.

| Integration | HangarKit target | Important distinction |
| --- | --- | --- |
| `order_admin` | `env`, `region` | Supports current-user or explicit owner mode and target-scoped `ensure_access`. |
| `promotion_admin` | `env`, `region` | Regional host; live/uat/test only. |
| `cmt_admin` | `env`, `region` | Its region list differs from Promotion Admin's. |
| `product_label_admin` | `env` | No region; SSP host. |
| `ssc_ops` | `env` | Business country/project are operation headers, **not** routing `region`. |
| `user_admin` | `env`, `region` | Region selects market context; upstream host remains global. |
| `listing_admin` | `env` | No region; stable and staging are supported. |
| `bd_centre` | `env` | Cookie-derived CSRF query value is injected by Connector. |
| `tws` | `env` | HangarKit currently routes Global only; Connector's CN/live route is not exposed. |
| `datasuite`, `seatalk_open`, `skyline`, `traffic_suite` | neither | Fixed hosts; Skyline is the test digital-QA host. |
| `cs_portal`, `dms_cs_portal` | `env`, `region` | Different portals and sessions; their regional set includes `xx`, `es`, `fr`, and `pl`. |
| `seller_sop` | `env`, `region` | Nine markets including CN; distinct from native Seller Portal. |
| `shopeefood_admin` | `env`, `region` | Five markets; no stable environment; Connector supplies CSRF headers. |
| `noti_admin`, `chat_admin` | `env` | Stable aliases staging; Chat Admin needs a compatible Relay CLI release. |
| `listing_qc_admin` | `env` | Separate Listing QC portal; Connector derives `sessionId`. |
| `soup` | `env` | Live/uat/test only, no region or credential export. |
| `leave_portal`, `mp_ai_dod` | neither | Fixed leave portal and staging AI DOD hosts. |
| `google_sites` | neither | Asynchronous page/asset jobs executed by an online local Relay browser. |

## Discover an operation before coding

In Craft, use `search_integration_operations(provider="<provider>", query=...)` and `describe_integration_operation(provider="<provider>", operation_id=...)`. The external app API also serves `GET /api/external/hangar/apps/:id/integrations/:provider/operations` and `GET .../operations/:operation_id` for all 24 Relay providers and the seven native providers in `connector_integration.native_apis`. These development-time catalog routes use the relevant app-scoped Connector grant; they are not app frontend functions. Alternatively, an authorized local CLI can run `connector api search --service <connector-service> <query>` and `connector api describe <connector-service> <operation-id>`. CLI research does **not** grant a Hangar app permission. Inspect method, path, request schema (`input.path`, `input.query`, `input.fixed_query`, `input.headers`, `input.fixed_headers`, `input.content_type`, `input.body`), output schema, source, maturity, risk, confirmation, and target. `discovered` means extracted from source, **not** verified with a real account. DataSuite and Skyline have no bundled operations at present; an empty result may also reflect a missing grant or catalog revision. Do not invent an endpoint from a blank result.

## Use the backend SDK

Configure `settings.integrations.<provider>` as `{"auth_mode":"user"}` (optionally `{"auth_mode":"user","required":true}` for a grant-only entry requirement). A current-user Connector consent screen can appear at app entry even when `required` is false; test that experience instead of promising optional means no consent. Each visitor supplies their own grant and website session.

Import the named Python module in an authenticated backend handler, for example `from hangarkit.integrations import ssc_ops`. Prefer `ssc_ops.call("listActiveAnnouncements", env="test", params={...}, headers={"X-Ops-Project": "sls"})` **when that operation is in the current catalog and its contract has been verified**. `call` resolves the operation from Hangar's app-scoped catalog, checks the service/method/path, required path/query/header fields and enums, injects fixed query/header values, applies declared request content type, and rejects unsupported upstream selectors. It never accepts a caller-chosen HTTP method or arbitrary URL. Pass `path_params` for `{name}` path placeholders, `params` for documented query fields, `json` or `data` for the body, and `headers` for documented business context. For `confirmation: required`, get explicit user confirmation *before* passing `confirm=True`; this is not a permission bypass. Validate inputs and keep the operation ID fixed on the server; do not expose a general catalog executor to the app frontend.

Use `provider.request("GET", "/verified/path", env=..., region=..., params=..., headers=...)` only for an uncataloged but independently verified endpoint or a contract `call` does not support. `get/post/put/patch/delete` remain shorthand for `request`, not the recommended discovery workflow. `client(config=None)` exposes the same methods for explicit configuration. Pass the provider page's exact target inputs, even where Connector CLI has defaults. Use only portal-relative paths; the SDK rejects absolute URLs and unsafe paths and does not accept unsupported env/region fields. Do not accept arbitrary path/method/headers, unrestricted filters, or write confirmation from visitors. Hangar and Connector own the credentials.

By default `call` and `request` return decoded JSON, a UTF-8 string for non-JSON content, or `None` for an empty body. With `full_response=True`, a successful call returns `{"status": 200, "status_text": "OK", "headers": {...}, "body_encoding": "json|text|base64", "body": ..., "diagnostics": [...]}`. Binary bodies are base64; response headers exclude session/auth/token headers. This flag changes **successful** output only: a non-2xx HTTP status **always raises** `provider.RelayPortalError`, including when `full_response=True`. It does not return an error response as a normal result.

## Read failures safely

Every `RelayPortalError` has `stage`, `response`, `diagnostics`, `user_message`, `support_details`, `recovery_url`, and `action_label`. `stage` is `validation` (local input/contract rejection), `catalog` (operation lookup), `request` (the intended portal call), or `access` (Order Admin `ensure_access`). A catalog failure in `call` can therefore have an HTTP status even though the **portal request was never sent**. For a non-2xx HTTP failure, `exc.response` has the same fields as a full response, including `status`, filtered `headers`, decoded/base64 `body`, and catalog response `diagnostics` (a list). Error bodies are capped at 16 KiB with optional `body_truncated: true`. The body is **not** scrubbed of business data. For a transport failure (no HTTP reply) or local validation error, `exc.response is None`; `stage` still identifies where it failed. Never access `exc.response["status"]` without checking for `None`.

For example, a failed portal request might have this `exc.response` (the exact body and headers depend on the upstream):

```json
{
  "status": 403,
  "status_text": "Forbidden",
  "headers": {"Content-Type": "application/json", "X-Request-ID": "example-id"},
  "body_encoding": "json",
  "body": {"error": "permission_denied"},
  "diagnostics": []
}
```

`exc.diagnostics` is a separate dictionary of allowlisted Connector/Hangar recovery metadata, often empty; look for `reason`, `next_action`, and `request_id` only when present. `exc.response["diagnostics"]` is instead a list of matching catalog response hints. `exc.user_message` falls back to `str(exc)` when no trusted recovery metadata exists; for a raw request error that fallback can contain the upstream body. Do **not** return or log `str(exc)`, `exc.user_message`, `exc.response["body"]`, or complete headers to an app visitor without reviewing and redacting them. Map known status/reason codes to short messages in the backend; keep a request ID for support.

```python
from hangarkit.integrations import order_admin

try:
    response = order_admin.call(
        "retrieve-current-authenticated-user-info",
        env="test", region="sg", full_response=True,
    )
    result = response["body"]  # HTTP 2xx; response["status"] is available here.
except order_admin.RelayPortalError as exc:
    http = exc.response  # None for local validation or a connection failure.
    if http is not None:
        status = http["status"]
        error_body = http["body"]              # Decoded JSON/text or base64.
        response_headers = http["headers"]     # Session/auth headers removed.
        body_encoding = http["body_encoding"]  # "json", "text", or "base64".
        truncated = http.get("body_truncated", False)
        # Inspect error_body and response_headers only in trusted backend code.
    else:
        status = None
        error_body = None
        response_headers = {}
    reason = exc.diagnostics.get("reason")
    request_id = exc.diagnostics.get("request_id")
    if exc.stage == "catalog":
        message = "The API catalog could not be read."
    elif status == 403:
        message = "Access was denied for this operation."
    else:
        message = "The operation could not be completed. Please retry."
    # Return only the reviewed message and optional request ID to the UI.
```

`get/post/put/patch/delete` are `request` shortcuts and follow the same success/exception rule. `search_operations`/`describe_operation` may raise with `stage="catalog"` on HTTP/transport failure. Order Admin `ensure_access` is different: a **successful HTTP response** can return `state="pending"`, `"denied"`, `"relay_offline"`, etc. Those are normal readiness results, not Python exceptions; it raises only on HTTP/transport/invalid-response failures. An earlier `ready` does not guarantee the next business operation succeeds.

For a non-sending request preview, use `call(..., preview=True)`: it resolves the catalog and validates inputs but returns only method, path **template**, target, query/header **names**, body presence/type, risk, and confirmation. It never returns parameter values, request body, tokens, cookies, or the resolved URL. Catalog resolution or validation can still raise; it does **not** send the portal request. `describe_operation` gives the complete declared outgoing request contract. Use the developer catalog during design, not on each frontend render.

For example, after describing a verified operation, a backend developer can inspect `provider.call("operation-id", env="test", preview=True, ...)` without confirming or sending even a write. They can then call it with `confirm=True` only after the app user confirms. `provider.call("operation-id", env="test", full_response=True, ...)` sends it and returns the **response**, not the outgoing request. To inspect caller-supplied body/header **values** while building, inspect and validate those values in your backend before calling HangarKit; do not log or return a complete authenticated request. Connector-managed session headers and cookies are never made available by the SDK.

`search_operations` and `describe_operation` are also available in the backend for these providers, but prefer Craft or the external app API for design-time discovery. Only Order Admin has `ensure_access`; the actual reviewed request is the access check for the selected target and operation elsewhere. Do not run a speculative preflight or block the whole app because Relay is offline. Show a feature-scoped loading/error/retry state; offer CLI setup only when a missing session actually needs the user's Relay. The shared `connector_integration.relay` page gives the user-facing explanation and recovery steps.

Verify at least one actual read with the intended runtime user and target before declaring an integration working; separately confirm write intent, permissions, and duplicate protection for mutations. A successful grant, paired device, cached session, or frontend build is not proof that a particular API succeeds.
## Related capabilities

- `backend.integrations`
- `connector_integration.relay`
- `connector_integration.order_admin`
- `connector_integration.promotion_admin`
- `connector_integration.cmt_admin`
- `connector_integration.product_label_admin`
- `connector_integration.ssc_ops`
- `connector_integration.user_admin`
- `connector_integration.listing_admin`
- `connector_integration.bd_centre`
- `connector_integration.tws`
- `connector_integration.datasuite`
- `connector_integration.seatalk_open`
- `connector_integration.skyline`
- `connector_integration.traffic_suite`
- `connector_integration.cs_portal`
- `connector_integration.dms_cs_portal`
- `connector_integration.seller_sop`
- `connector_integration.shopeefood_admin`
- `connector_integration.noti_admin`
- `connector_integration.chat_admin`
- `connector_integration.listing_qc_admin`
- `connector_integration.soup`
- `connector_integration.leave_portal`
- `connector_integration.mp_ai_dod`
- `connector_integration.google_sites`
