# TWS

ID: `connector_integration.tws`
Category: `connector_integration`

Use the Global TWS environments supported by HangarKit and distinguish Connector's separate CN/live route.

## Import

`from hangarkit.integrations import tws`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `tws.call(operation_id, *, env, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, full_response=False, preview=False)`
- `tws.request(method, path, *, env=None, region=None, params=None, json=None, data=None, headers=None, timeout=30, auth_mode=None, full_response=False)`
- `tws.get(path, **kwargs)`
- `tws.post(path, **kwargs)`

## Details

## Do not conflate Global and CN

TWS is a standalone current-user Craft integration. Relay can refresh the visitor's website session when required, while a cached session can work with Relay offline. Read `connector_integration.relay` to explain Connector grant, browser sign-in, and recovery to a newcomer. This provider has no owner mode or HangarKit `ensure_access`; catalog-backed `call` is supported for the Global route.

HangarKit requires `env` (`live`, `uat`, `test`, `staging`) and routes to **Global** `tws.shopeemobile.com` or `tws.<env>.shopeemobile.com`. It rejects `region`; do not add a CN choice to a Hangar app built on this SDK. Connector CLI/backend **also** support CN live at `tws.shopeesz.com` via a separate `tws_cn/live` proxy route and target-specific cache, but that route is **not exposed by the current HangarKit TWS module**. CN non-live is unsupported. Never claim a Global success means CN is ready. If CN is needed, request a reviewed HangarKit/proxy change before building that feature.

The portal kit probes `/api/v2/user/login_info/search` using specific warehouse/operation-mode context headers and captures session/CSRF material. Connector injects the cookie-derived `x-csrftoken` header for proxied requests. Do not read the cookie or supply a fabricated CSRF token; some business operations need additional context headers, which must come from the operation contract.

## Build and recover

Search/describe `provider="tws"` in Craft's app-scoped catalog (or use `connector api search/describe --service tws`). Check request fields, warehouse/operation-mode headers, maturity, write risk, and confirmation. Prefer `tws.call(operation_id, env=env, headers=reviewed_context)` for a verified catalog operation in a narrow authenticated backend action. Use `request` only for independently verified uncataloged Global endpoints. See `relay_portals` for full response and redacted preview. Server-validate warehouse scope and inputs; a discovered TWS write is not a tested contract.

Configure `settings.integrations.tws` as `{"auth_mode":"user"}`. `required:true` is a grant-only entry condition; optional user-mode consent may still prompt. Surface a scoped retry and the shared Relay recovery steps for missing sessions, and distinguish warehouse/permission denial from local Relay setup. Test the intended Global environment and actual operation as a runtime visitor before saying it works.
## Quick examples

- `tws.get("/api/v2/user/login_info/search", env="uat")`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
