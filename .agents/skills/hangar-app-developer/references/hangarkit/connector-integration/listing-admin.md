# Listing Admin

ID: `connector_integration.listing_admin`
Category: `connector_integration`

Build Listing Admin workflows on an explicitly chosen environment and current-user website session.

## Import

`from hangarkit.integrations import listing_admin`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `listing_admin.call(operation_id, *, env, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, full_response=False, preview=False)`
- `listing_admin.request(method, path, *, env=None, region=None, params=None, json=None, data=None, headers=None, timeout=30, auth_mode=None, full_response=False)`
- `listing_admin.get(path, **kwargs)`
- `listing_admin.post(path, **kwargs)`

## Details

## Understand access and target

Listing Admin is its own Craft integration. The current app user approves the app's Connector access; Relay can refresh that user's portal session on a paired computer if needed. Read `connector_integration.relay` for the user-facing explanation and recovery flow. Cached access may work while Relay is offline. There is no owner mode or HangarKit `ensure_access`; catalog-backed `call` is supported.

Supply `env` for every SDK call: `live`, `uat`, `test`, `staging`, or `stable`. The host is `admin.listing.shopee.com` for live and `admin.listing.<env-prefix>shopee.com` for others (`stable` uses `test-stable.`). The SDK does not accept `region`; choosing a marketplace in the browser is not an SDK routing parameter and may require an operation-specific input. Connector CLI's default `uat` is not the SDK default. `/wsa/api/v1/auth/info` is the portal session probe, not proof that a listing mutation is permitted.

## Select an operation

Search/describe `provider="listing_admin"` in Craft's app-scoped catalog (or use `connector api search --service listing-admin` with optional `--page-url`). Check required inputs, maturity, risk, and confirmation; discovered frontend calls need independent verification. Prefer `listing_admin.call(operation_id, env=env, ...)` for a verified catalog operation in an authenticated backend route; use `request` for independently verified uncataloged endpoints. See `relay_portals` for full response and redacted preview. Keep operation ID and validated query/body under server control. Do not send credentials or a generic portal proxy to the frontend.

Configure `settings.integrations.listing_admin` with `{"auth_mode":"user"}`. `required:true` gates on the Connector grant only, and optional current-user integrations may still prompt for consent at entry. If a request fails, distinguish consent, pending session, permission denial, and transport issues; keep retry and Relay help within the affected feature. Test the real operation in every environment exposed by the app.
## Quick examples

- `listing_admin.get("/wsa/api/v1/auth/info", env="uat")`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
