# CMT Admin

ID: `connector_integration.cmt_admin`
Category: `connector_integration`

Use CMT Admin's own regional target set and current-user Relay session in a Hangar app.

## Import

`from hangarkit.integrations import cmt_admin`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `cmt_admin.call(operation_id, *, env, region, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, full_response=False, preview=False)`
- `cmt_admin.request(method, path, *, env=None, region=None, params=None, json=None, data=None, headers=None, timeout=30, auth_mode=None, full_response=False)`
- `cmt_admin.get(path, **kwargs)`
- `cmt_admin.post(path, **kwargs)`

## Details

## Start with the person and target

CMT Admin is a separate Craft integration, not Promotion Admin with a different URL. It uses the **current visitor's** Connector grant and website access. Relay is the background helper that can renew their browser session; an already cached session may work without an online Relay. Read `connector_integration.relay` to explain this to a first-time user and to give local setup steps only when needed. There is no owner mode or provider `ensure_access` in HangarKit.

The SDK requires `env` (`live`, `uat`, `test`) and `region` (`ar`, `br`, `cl`, `co`, `es`, `fr`, `id`, `kh`, `la`, `mm`, `mx`, `my`, `ph`, `pl`, `sg`, `th`, `tw`, `vn`) **on each request**. Do not use Promotion Admin's `xx` here; CMT supports `es`, `fr`, and `pl` instead. `staging`/`stable` are unsupported. Connector CLI's default `uat/sg` is not applied by the SDK. The selected pair maps to a `cmt-admin.<env>shopee<regional-suffix>` host; `/api/v1/auth/info` is a target-specific authentication probe, not business authorization.

## Build a feature

Search and describe `provider="cmt_admin"` in Craft's app-scoped catalog (or use `connector api search/describe --service cmt-admin` in a locally authorized CLI). Inspect method, path, required input, maturity, and risk. Prefer `cmt_admin.call(operation_id, env=env, region=region, params=filters)` for a verified catalog operation in an authenticated backend action with server-validated filters. `request` is for independently verified uncataloged endpoints. See `relay_portals` for full response and redacted request preview. The default returns JSON, text, or `None`; HTTP errors raise `RelayPortalError`. Never relay arbitrary paths from the frontend or assume a discovered write is production-ready.

Set `settings.integrations.cmt_admin` to `{"auth_mode":"user"}`. `required:true` is only a Connector-grant entry rule; even optional user-mode integrations may trigger general consent before the app loads. If the operation fails, show a scoped explanation and retry, and follow `connector_integration.relay` for missing-grant, pending-session, Relay, and website-denial handling. Verify the actual request as the intended user for each target the app offers.
## Quick examples

- `cmt_admin.get("/api/v1/auth/info", env="test", region="fr")`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
