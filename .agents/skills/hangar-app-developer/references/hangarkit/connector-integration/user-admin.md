# User Admin

ID: `connector_integration.user_admin`
Category: `connector_integration`

Use User Admin's required market context on its shared environment host with current-user consent.

## Import

`from hangarkit.integrations import user_admin`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `user_admin.call(operation_id, *, env, region, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, full_response=False, preview=False)`
- `user_admin.request(method, path, *, env=None, region=None, params=None, json=None, data=None, headers=None, timeout=30, auth_mode=None, full_response=False)`
- `user_admin.get(path, **kwargs)`
- `user_admin.post(path, **kwargs)`

## Details

## Separate environment, market, and permission

User Admin is a standalone Craft integration using the **current app user's** Connector grant and portal session. Relay on their paired computer can refresh a missing session, but a cached session may succeed when Relay is offline. Read `connector_integration.relay` for a newcomer-friendly explanation and local setup only when prompted. This provider does not support owner mode or `ensure_access`; it does support catalog-backed `call`.

The SDK requires `env` (`live`, `uat`, `test`, `staging`, `stable`) and `region` (`sg`, `id`, `th`, `tw`, `br`, `ph`, `my`, `vn`, `mx`, `co`, `cl`, `pl`, `ar`, `kh`, `la`, `mm`). Its `admin.user.<env>shopee.io` host changes with **environment, not region**. Region is the market context for the portal and Relay target; an API may separately require a `region` value in query/body or a business header. Inspect the operation rather than presuming HangarKit injects it. Connector CLI's `uat/sg` defaults do not remove the SDK's explicit-input requirement. The portal's `/api/v1/auth/info` checks sign-in, not access to sensitive account operations.

## Build with care

Search/describe `provider="user_admin"` in Craft's app-scoped catalog (or use `connector api search/describe --service user-admin`) for method, relative path, input schema, maturity, and risk. Some operations expose or alter sensitive user data; do not infer permissions from a sign-in probe or publish a discovered write without contract/authorization testing. Prefer `user_admin.call(operation_id, env=env, region=region, ...)` for a fixed verified operation behind an authenticated backend route; use `request` only for an independently verified uncataloged endpoint. See `relay_portals` for full response and safe preview. Validate any separately required market field and never forward a visitor-supplied arbitrary path or return sensitive data unnecessarily.

Set `settings.integrations.user_admin` to `{"auth_mode":"user"}`; `required:true` is a grant-only entry rule. Optional current-user consent may still occur before the app loads. When the actual request fails, show a scoped retry or permission guidance, and use the shared Relay guide for missing sessions; a website denial is not fixed by repeatedly reopening the browser. Test as the intended visitor in the environment and market the feature offers.
## Quick examples

- `user_admin.get("/api/v1/auth/info", env="test", region="sg")`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
