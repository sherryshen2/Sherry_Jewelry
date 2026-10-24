# Listing QC Admin

ID: `connector_integration.listing_qc_admin`
Category: `connector_integration`

Use the separate Listing QC portal with environment routing and Connector-managed sessionId.

## Import

`from hangarkit.integrations import listing_qc_admin`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `listing_qc_admin.call(operation_id, *, env, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`
- `listing_qc_admin.request(method, path, *, env, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`

## Details

Read the shared Relay overview and portal API contract. Listing QC Admin is its own current-user integration, not Listing Admin with a different page. Grant, account permission, and website session are separate; no owner mode or `ensure_access` is supported. A cached session may work offline.

Require `env` (`live`, `test`, `uat`, `staging`, `stable`) and do not pass `region`. Hosts are `listingqc.<env-prefix>shopee.io`; stable uses `test-stable.`. Connector derives the `sessionId` header from the stored site session. App code must not obtain cookies or manufacture that header. Operation-specific marketplace/project values are separate inputs.

Search/describe `provider="listing_qc_admin"` and review quality-control actions, fields, maturity, and risk before implementing. Prefer `call` for verified operations; use `request` only for independently maintained uncataloged paths. Validate scope and confirm mutations, including bulk moderation/decision actions. Use common exceptions, filtered response handling, and feature-local recovery. Test the real action, not just the sign-in probe.
## Quick examples

- `listing_qc_admin.get("/wsa/api/v1/auth/info", env="test")`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
- `connector_integration.listing_admin`
