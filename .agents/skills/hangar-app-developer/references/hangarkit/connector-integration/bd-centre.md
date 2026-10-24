# BD Centre

ID: `connector_integration.bd_centre`
Category: `connector_integration`

Build BD Centre operations with environment routing and Connector-managed session/CSRF handling.

## Import

`from hangarkit.integrations import bd_centre`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `bd_centre.call(operation_id, *, env, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, full_response=False, preview=False)`
- `bd_centre.request(method, path, *, env=None, region=None, params=None, json=None, data=None, headers=None, timeout=30, auth_mode=None, full_response=False)`
- `bd_centre.get(path, **kwargs)`
- `bd_centre.post(path, **kwargs)`

## Details

## Explain access

BD Centre is a standalone current-user Craft integration. Connector checks that this app may use the visitor's access; browser Relay can establish that visitor's portal session if required. Read `connector_integration.relay` for the consent and local recovery story; do not ask every visitor to install CLI in advance. A cached request can succeed with Relay offline. Owner mode and `ensure_access` are not provided; catalog-backed `call` is available.

Every request needs `env`: `live`, `uat`, `test`, or `staging`. **No** `stable` and **no** SDK `region`. Targets use `bd-centre.shopee.com` (live) or `bd-centre.<env>.shopee.com`; Connector CLI's default `uat` is not applied by HangarKit. The portal kit uses `/api/admin/bd_center/v1/my/info/` for a session probe. Connector attaches a cookie-derived `CSRF_TOKEN` **query parameter** where applicable; do not read cookies or manufacture that token in app code. A business `region` field in a specific operation is different from a routing region.

## Discover and implement

Search/describe `provider="bd_centre"` in Craft's app-scoped catalog (or use `connector api search/describe --service bd-centre`) to check exact method, path, inputs, maturity, risk, and confirmation; a mechanically extracted operation may not have been verified upstream. Prefer `bd_centre.call(operation_id, env=env, ...)` for a verified catalog operation through an authenticated backend action with server-side input validation. Use `request` for an independently verified uncataloged endpoint. `params` carries business query fields while Connector owns session/CSRF handling; see `relay_portals` for full response and safe preview. Keep app users away from arbitrary paths or write APIs.

Set `settings.integrations.bd_centre` to `{"auth_mode":"user"}`; `required:true` gates the app grant, not a live session. The general current-user consent flow can prompt even when optional. If the real operation fails, offer feature-scoped retry and grant/session/permission guidance from the shared Relay page. Test the operation as the intended visitor in each offered environment, including any required business context.
## Quick examples

- `bd_centre.get("/api/admin/bd_center/v1/my/info/", env="uat")`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
