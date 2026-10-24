# DataSuite

ID: `connector_integration.datasuite`
Category: `connector_integration`

Use DataSuite's fixed host and current-user browser session without inventing target options or catalog operations.

## Import

`from hangarkit.integrations import datasuite`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `datasuite.call(operation_id, *, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, full_response=False, preview=False)`
- `datasuite.request(method, path, *, env=None, region=None, params=None, json=None, data=None, headers=None, timeout=30, auth_mode=None, full_response=False)`
- `datasuite.get(path, **kwargs)`
- `datasuite.post(path, **kwargs)`

## Details

## Explain the moving parts

DataSuite is its own Craft integration. Connector checks the **current app user's** grant and sends approved requests using that person's website session. Browser Relay on their paired computer may restore a missing session; cached access can succeed while Relay is offline. Read `connector_integration.relay` to explain consent versus sign-in and the local setup steps to a first-time user. This integration cannot use the app owner's account and has no HangarKit `ensure_access`. Catalog-backed `call` is available when the active catalog contains an operation.

DataSuite has one fixed upstream host, `datasuite.shopee.io`. Pass **neither** `env` nor `region` to the SDK: both are rejected. The portal kit identifies `/datasuite-homepage/api/v1/users/me` as the current-user/session probe. A successful probe does not demonstrate permission for a particular dataset or report.

## Design the feature

The Connector catalog lists `datasuite` as a Relay integration, but the bundled catalog currently has **no DataSuite operations**. Search `provider="datasuite"` in Craft or use the authorized `connector api search --service datasuite <task>` to confirm the active catalog. Do not guess a report or export endpoint from this page. When a reviewed catalog operation exists, use `datasuite.call(operation_id, ...)`; otherwise obtain an independently maintained upstream contract and verify method, path, inputs, permissions, and response before using `datasuite.request(...)` in an authenticated backend route. See `relay_portals` for full response and safe preview. The example checks the authenticated user, not a business workflow. Expose only reviewed actions, never a generic URL/method proxy to the frontend.

Configure `settings.integrations.datasuite` as `{"auth_mode":"user"}`. `required:true` checks the Connector grant at entry, not website readiness; even optional current-user integrations may show general consent first. When an actual operation fails, distinguish missing grant, pending Relay/session work, report-specific denial, and transient failure. Give a feature-scoped retry and the shared Relay guidance only when necessary. Verify the real requested operation with the intended visitor; a cached session or sign-in probe is not end-to-end proof.
## Quick examples

- `datasuite.get("/datasuite-homepage/api/v1/users/me")`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
