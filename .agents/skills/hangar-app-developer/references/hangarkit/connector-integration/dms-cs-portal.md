# DMS CS Portal

ID: `connector_integration.dms_cs_portal`
Category: `connector_integration`

Use the separately authenticated DMS CS Portal and its regional API contracts.

## Import

`from hangarkit.integrations import dms_cs_portal`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `dms_cs_portal.call(operation_id, *, env, region, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`
- `dms_cs_portal.request(method, path, *, env, region, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`

## Details

Read `connector_integration.relay` and `relay_portals` first. DMS CS Portal is a separate integration and session from the in-house CS Portal, not a URL substitution for `cs_portal`. Each visitor uses their current-user grant and DMS account. No owner mode or `ensure_access` is supported; a cached session can work with Relay offline.

Both `env` and `region` are required. Environments: `live`, `uat`, `test`, `staging`, `stable`. Regions: `ar`, `br`, `cl`, `co`, `es`, `fr`, `id`, `kh`, `la`, `mm`, `mx`, `my`, `ph`, `pl`, `sg`, `th`, `tw`, `vn`, `xx`. The host family is `dms.cs.<env-prefix>shopee<regional-suffix>`, with `test-stable.` for stable. The current-user endpoint above is a session probe, not DMS business authorization. Do not copy CS Portal cookie or API assumptions.

Search/describe `provider="dms_cs_portal"`, then call a reviewed operation in an authenticated backend route. Validate tenant, account, and case/resource scope; never expose a generic DMS proxy or sensitive response data to arbitrary visitors. Use the common full-response/error handling, explicit write confirmation, and feature-local recovery. Ask for local Relay setup only when missing access actually requires it, and verify the real API with the intended DMS user.
## Quick examples

- `dms_cs_portal.get("/api/v1/users/current", env="test", region="sg")`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
- `connector_integration.cs_portal`
