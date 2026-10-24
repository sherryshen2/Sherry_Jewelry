# CS Portal

ID: `connector_integration.cs_portal`
Category: `connector_integration`

Use regional in-house CS Portal APIs with the current user's grant and website session.

## Import

`from hangarkit.integrations import cs_portal`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `cs_portal.call(operation_id, *, env, region, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`
- `cs_portal.request(method, path, *, env, region, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`

## Details

Read the shared Relay concept and portal API pages first. CS Portal is its own current-user integration: each visitor approves this app and uses their own CS website permission. There is no owner mode or `ensure_access`. A grant is not a CS agent entitlement; Relay can restore a missing session, while an already valid cached session may work offline.

Supply both `env` and `region`. Environments are `live`, `uat`, `test`, `staging`, `stable`; regions are `ar`, `br`, `cl`, `co`, `es`, `fr`, `id`, `kh`, `la`, `mm`, `mx`, `my`, `ph`, `pl`, `sg`, `th`, `tw`, `vn`, `xx`. The target is `cs.<env-prefix>shopee<regional-suffix>`; stable uses `test-stable.`. HangarKit does not use Connector CLI defaults. The current-agent probe above is not proof of access to every case, customer, or workstation action.

Search/describe `provider="cs_portal"` and prefer `call` for verified operations. Use `request` only for independently reviewed relative endpoints. Bound identifiers, filters, and results in an authenticated backend action; CS data is sensitive. `required:true` concerns app consent, not live Relay or all target sessions. Follow the common response/exception/recovery contract and give feature-scoped retry, not a global Relay blocker. Test the actual operation as the intended CS user and target.
## Quick examples

- `cs_portal.get("/api/inhouse/account/v1/agent/current", env="test", region="sg")`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
- `connector_integration.dms_cs_portal`
