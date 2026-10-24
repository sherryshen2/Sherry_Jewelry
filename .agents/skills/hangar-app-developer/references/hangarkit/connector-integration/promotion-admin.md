# Promotion Admin

ID: `connector_integration.promotion_admin`
Category: `connector_integration`

Build regional Promotion Admin features with current-user consent and a verified portal API contract.

## Import

`from hangarkit.integrations import promotion_admin`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `promotion_admin.call(operation_id, *, env, region, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, full_response=False, preview=False)`
- `promotion_admin.request(method, path, *, env=None, region=None, params=None, json=None, data=None, headers=None, timeout=30, auth_mode=None, full_response=False)`
- `promotion_admin.get(path, **kwargs)`
- `promotion_admin.post(path, **kwargs)`

## Details

## What a builder and user need to know

Promotion Admin is a standalone Craft integration. Connector carries approved portal requests for the **current app user**; Relay may establish that person's browser session on their paired computer when no usable session exists. Read `connector_integration.relay` for a plain-language explanation, download/setup instructions, consent, and recovery. A saved session may work when Relay is offline. Owner mode, service credentials, and Order Admin's `ensure_access` are not supported here; catalog-backed `call` is available.

## Select the target

Supply **both** `env` and `region` for every HangarKit request. Environments: `live`, `uat`, `test`; regions: `id`, `sg`, `my`, `th`, `tw`, `ph`, `vn`, `br`, `xx`, `mx`, `co`, `cl`, `ar`, `kh`, `mm`, `la`. `staging` and `stable` are not supported. Connector's default `uat/sg` is not a HangarKit default: the SDK requires explicit values. Each pair routes to a separate `admin.promotion.<env>shopee<regional-suffix>` host and can have its own session and business permission. The Connector portal kit identifies `/api/v1/auth/info` as its authentication-info endpoint; it does not prove access to another Promotion API.

## Discover, implement, and recover

Use Craft's app-scoped search/describe tools with `provider="promotion_admin"` or `connector api search/describe --service promotion-admin` during development. Confirm method, relative path, schema, maturity, risk, and confirmation; do not infer a promotion write payload from the website. Prefer `promotion_admin.call(operation_id, env=env, region=region, ...)` for a verified catalog operation in an authenticated backend route; use `request` only for independently verified uncataloged contracts. `params` handles query fields; `json` or `data` handles a body. See `relay_portals` for full response and safe preview. Expose a narrow app action rather than a generic proxy. The `get` example above is an auth probe, not a guarantee that a campaign operation works.

Configure `settings.integrations.promotion_admin` with `{"auth_mode":"user"}`; `required:true` checks the grant at app entry, not the target session. Consent may also be requested for an optional current-user integration. On failure, distinguish missing app grant from a portal access denial or Relay/session work using safe error diagnostics; show a retry for the affected feature. Do not ask for CLI installation merely because Relay is offline if a cached request succeeds. Test the actual selected env/region and operation as the intended user before declaring the feature ready.
## Quick examples

- `promotion_admin.get("/api/v1/auth/info", env="test", region="sg")`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
