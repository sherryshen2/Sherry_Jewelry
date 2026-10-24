# SSC Ops

ID: `connector_integration.ssc_ops`
Category: `connector_integration`

Route SSC Ops by environment and supply operation-specific project and country headers separately.

## Import

`from hangarkit.integrations import ssc_ops`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `ssc_ops.call(operation_id, *, env, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, full_response=False, preview=False)`
- `ssc_ops.request(method, path, *, env=None, region=None, params=None, json=None, data=None, headers=None, timeout=30, auth_mode=None, full_response=False)`
- `ssc_ops.get(path, **kwargs)`
- `ssc_ops.post(path, **kwargs)`

## Details

## Choose the website and business context

SSC Ops is a standalone current-user integration. The visitor grants this app Connector access; a local Relay may obtain their website session only when necessary. Read `connector_integration.relay` to explain grant versus sign-in and the beginner's recovery steps. A cached session can work without an online Relay. Owner mode and HangarKit `ensure_access` are unavailable; catalog-backed `call` is supported.

Pass `env="test"`, `"uat"`, or `"live"` on every HangarKit request; the SDK requires it even though Connector CLI defaults to test. The portal hosts are `ops.ssc.test.shopeemobile.com`, `ops.ssc.uat.shopeemobile.com`, and `ops.ssc.shopeemobile.com`. **No routing `region` parameter exists.** SSC's selected project and business country are separate API context: catalog operations can require `X-Ops-Project` (for example `sls` or `finance`) and `X-Ops-Sub-App-Country` (for example `SG`, `TH`, or `AR`). Never treat a browser country selection as proof that these headers were forwarded. The portal's session probe uses `/api/v3/ops/page-init` with `x-ops-project: sls`; different business actions may need other headers.

## Discover the specific API

Use Craft's app-scoped catalog with `provider="ssc_ops"` or `connector api search/describe --service ssc-ops` while designing. Many records are mechanically `discovered`, not runtime verified. Check documented method, path, required context headers, schema, and write risk. For a **verified** operation use `ssc_ops.call(operation_id, env=env, headers={"X-Ops-Project": project, "X-Ops-Sub-App-Country": country})` in a narrow authenticated backend action; the server must allowlist project and country. Catalog fixed headers are added automatically. Use `request` only for an independently verified uncataloged endpoint. See `relay_portals` for full response and redacted preview. Do not forward arbitrary client headers or trust user-selected values as permissions.

Configure `settings.integrations.ssc_ops` with `{"auth_mode":"user"}`. `required:true` checks the grant at app entry, not the project/country permission or session; optional current-user consent may still appear. Handle a failed operation with a local retry and a message distinguishing grant, pending session/Relay, portal denial, and business-context error. Validate the actual API with the intended user, environment, project, and country before announcing it works.
## Quick examples

- `ssc_ops.get("/api/v3/ops/page-init", env="test", headers={"x-ops-project":"sls"})`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
