# Native Connector APIs

ID: `connector_integration.native_apis`
Category: `connector_integration`

Build native linked-account integrations without confusing app consent, provider credentials, or browser Relay.

## Import

`from hangarkit.integrations import gitlab, figma, notion, grafana, sea_transify, seller_portal, smart`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `provider.call(operation_id, *, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`
- `provider.request(method, path, *, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`
- `provider.get(path, **kwargs), provider.post(path, **kwargs), provider.put(path, **kwargs), provider.patch(path, **kwargs), provider.delete(path, **kwargs)`
- `provider.search_operations(query="", *, timeout=30)`
- `provider.describe_operation(operation_id, *, timeout=30)`

## Details

These seven are separate integrations in Craft. Connector forwards API calls with the selected person's linked OAuth credential, token, or stored account configuration. They do not use Hangar's browser Relay setup, do not require a local Relay worker, and have no `ensure_access`. Linking a provider account is different from giving this Hangar app a Connector grant. Neither proves permission for every upstream operation.

Hangar defaults these native providers to `{"auth_mode":"app","app_provider":"owner_token"}`. This uses the actual app owner's linked account, shared only through app actions. Explain that choice and obtain owner consent. Configure `{"auth_mode":"user"}` when each visitor should use their own account. Only these two modes are supported by the new SDK modules; do not paste service tokens or cookies into their configs. They require Connector and never fall back to Wingman. Preserve explicit saved account choices.

Account selection is an app setting, not a per-request credential override. Client-side configuration or headers cannot change the credential subject chosen by Hangar's server. The named provider page adds provider-specific supported parameters such as GitLab's `domain_id`.

`required:true` is a grant requirement, not a provider-readiness check. Required owner mode waits for the owner, not visitor approval. Current-user integrations can still prompt for platform consent at entry even when optional in the current gateway. Do not promise that optional means a consent-free first screen. Account denial, expired credentials, and provider outages belong in the affected feature's recovery UI.

## Discover and call

During development, use Craft's `search_integration_operations` / `describe_integration_operation`, or the authenticated external app API at `/api/external/hangar/apps/:id/integrations/:provider/operations`. The selected user's or owner's app-scoped grant filters the results. These are design-time tools; never expose a generic operation executor to the frontend. Inspect method, relative path, input shape, fixed fields, maturity, risk, and confirmation. `discovered` does not mean verified.

Prefer `provider.call(operation_id, ...)` for a reviewed catalog operation. It resolves the operation, injects fixed query/header values and declared content type, validates required path/query/business headers and enums, and rejects unsupported upstream selectors. Obtain user confirmation before passing `confirm=True` for a required write. `preview=True` checks the catalog and inputs without sending the provider operation and returns only target, method, path template, field names, body presence/type, risk, and confirmation.

Use `request` or its HTTP shortcuts for a maintained, independently verified uncataloged contract. Figma, Notion, and Seller Portal have proxies but no bundled catalog entries at present; an empty search is not permission to invent an operation ID. All seven reject `env` and `region`. Only GitLab accepts optional `domain_id`, a configured target ID rather than a hostname. Use numeric GitLab resource IDs when an encoded namespace would require a slash inside one path parameter. Do not accept arbitrary URLs, paths, headers, targets, or privileged actions from the UI.

## Responses and errors

The default result is decoded JSON, text, or `None` for an empty body. `full_response=True` returns `status`, `status_text`, filtered response `headers`, `body_encoding` (`json`, `text`, `base64`), `body`, and response `diagnostics` (a list). Authentication, cookie, and token headers are removed. Bodies can still contain private data.

Non-2xx always raises `provider.ConnectorError`, even with `full_response=True`. This aliases the shared transport error class. `exc.response` is the HTTP envelope with a capped error body and optional `body_truncated`, or `None` when there is no HTTP response. `exc.stage` distinguishes `catalog`, `request`, and `validation`; `exc.diagnostics` is a separate recovery dictionary, often empty. `exc.user_message` can fall back to a raw exception string, so do not return it or the raw body to visitors without review.

```python
from hangarkit.integrations import gitlab

try:
    result = gitlab.get("/api/v4/user", full_response=True)
except gitlab.ConnectorError as exc:
    http = exc.response
    status = http["status"] if http is not None else None
    error_body = http["body"] if http is not None else None
    response_headers = http["headers"] if http is not None else {}
    request_id = exc.diagnostics.get("request_id")
    # Keep raw provider data in trusted backend handling; return a reviewed message.
```

Distinguish app-grant recovery from reconnecting one linked provider account. In owner mode, visitors cannot repair the owner's credential. Return safe messages, retry controls, and a support request ID. Do not automatically retry a mutation after a transport failure with an unknown outcome. Verify a real authorized read and any offered mutation before claiming the app works; successful catalog search alone is not end-to-end proof.
## Related capabilities

- `backend.integrations`
- `connector_integration.gitlab`
- `connector_integration.figma`
- `connector_integration.notion`
- `connector_integration.grafana`
- `connector_integration.sea_transify`
- `connector_integration.seller_portal`
- `connector_integration.smart`
