# Product Label Admin

ID: `connector_integration.product_label_admin`
Category: `connector_integration`

Use the environment-scoped Product Label Admin portal without inventing a region selector.

## Import

`from hangarkit.integrations import product_label_admin`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `product_label_admin.call(operation_id, *, env, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, full_response=False, preview=False)`
- `product_label_admin.request(method, path, *, env=None, region=None, params=None, json=None, data=None, headers=None, timeout=30, auth_mode=None, full_response=False)`
- `product_label_admin.get(path, **kwargs)`
- `product_label_admin.post(path, **kwargs)`

## Details

## Access and routing

Add Product Label Admin as its own Craft integration. The **current app user** approves Connector access; Relay can refresh that user's website session if necessary. Read `connector_integration.relay` before explaining setup to someone who has never used Connector. A successful grant is not website permission, and a cached session may work with Relay offline. This integration has no owner mode or HangarKit `ensure_access`; catalog-backed `call` is supported.

Pass `env` on every request: `live`, `uat`, or `test`. Do **not** pass `region`; the SDK rejects it. The host is `productlabel.ssp.shopee.io` (live), `productlabel.ssp.uat.shopee.io`, or `productlabel.ssp.test.shopee.io`. Connector CLI may default to `uat`, but HangarKit does not. `/wsa/api/v1/auth/info` is the reviewed sign-in probe; it does not authorize every label operation.

## Build and test

During development, search/describe `provider="product_label_admin"` in Craft's app-scoped catalog (or use the authorized `connector api search/describe --service product-label-admin` CLI) to check exact method, path, body, maturity, and confirmation. In an authenticated backend route, prefer `product_label_admin.call(operation_id, env=env, ...)` for a **verified** catalog operation with server-validated input; use `request` for independently verified uncataloged contracts. `params` supplies query values, and `json` or `data` supplies the body. See `relay_portals` for full response and safe preview. Never expose the raw proxy, cookies, or auth headers to the browser.

Configure `settings.integrations.product_label_admin` as `{"auth_mode":"user"}`. `required:true` requires the grant, not a live Relay or a session for each environment; general current-user consent may also appear when optional. If access fails, show a feature-level retry and the relevant grant, website access, or Relay recovery step from `connector_integration.relay`. Test a real operation as a visitor in each offered environment; auth-info or a green device alone is insufficient.
## Quick examples

- `product_label_admin.get("/wsa/api/v1/auth/info", env="test")`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
