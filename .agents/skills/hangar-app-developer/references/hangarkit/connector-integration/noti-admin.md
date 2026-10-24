# Noti Admin

ID: `connector_integration.noti_admin`
Category: `connector_integration`

Use environment-scoped notification administration APIs without inventing a regional target.

## Import

`from hangarkit.integrations import noti_admin`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `noti_admin.call(operation_id, *, env, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`
- `noti_admin.request(method, path, *, env, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`

## Details

Read `connector_integration.relay` and `relay_portals` first. Noti Admin is a separate current-user integration. The visitor approves the app and supplies notification-portal access; Relay may renew a missing session. Cached access can work offline. Owner mode and `ensure_access` are unavailable.

Require `env`: `live`, `test`, `uat`, `staging`, or `stable`; reject routing `region`. The host family is `admin.noti.<env-prefix>shopee.io`. Notably stable maps to the staging host, not `test-stable.`. The SDK requires an explicit environment even if another tool has a default. A region/country field within a notification operation is business input, not a HangarKit routing selector.

Search/describe `provider="noti_admin"` and review request type, audience scope, maturity, risk, and confirmation before calling. Notification send/update/delete actions must be server-owned and explicitly confirmed as appropriate; do not guess schemas from the website. The common exception/full-response and feature-scoped recovery contracts apply. Verify a real safe operation and separately test any mutation; the auth-info probe is not end-to-end proof.
## Quick examples

- `noti_admin.get("/api/v1/auth/info", env="test")`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
