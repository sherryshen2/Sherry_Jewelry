# Traffic Suite

ID: `connector_integration.traffic_suite`
Category: `connector_integration`

Use Traffic Suite's fixed live portal with current-user grant, IDaaS sign-in, and operation-specific validation.

## Import

`from hangarkit.integrations import traffic_suite`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `traffic_suite.call(operation_id, *, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, full_response=False, preview=False)`
- `traffic_suite.request(method, path, *, env=None, region=None, params=None, json=None, data=None, headers=None, timeout=30, auth_mode=None, full_response=False)`
- `traffic_suite.get(path, **kwargs)`
- `traffic_suite.post(path, **kwargs)`

## Details

## Explain access

Traffic Suite is its own Craft integration. The **current app user** grants Connector access, and a browser-backed session on their paired Relay may be needed for `trafficsuite.shopee.io`. Its sign-in flow can start on `idaas.shopee.io` and return to Traffic Suite. The app never receives the person's password or cookies. Read `connector_integration.relay` for beginner-friendly consent and recovery steps. A cached session can still work when Relay is offline. Owner mode and `ensure_access` are not available; catalog-backed `call` is supported.

The Traffic Suite upstream host is fixed; **no** `env` or `region` SDK fields exist. Passing them is rejected. The portal kit uses `/tracking-gateway/tms-user-service/api/login` as its session probe. An IDaaS login or this probe alone does not prove permission for a tracking design or mutation.

## Use a reviewed operation

During development search/describe `provider="traffic_suite"` in Craft's app-scoped catalog (or use `connector api search/describe --service traffic-suite`) to inspect method, path, fields, maturity, risk, and confirmation. A catalog record may only be discovered from portal source; verify it with an authorized account. Expose a narrowly scoped authenticated backend action that prefers `traffic_suite.call(operation_id, ...)` for a verified catalog operation; `request` is for independently verified uncataloged endpoints. See `relay_portals` for full response and safe preview. Require explicit confirmation and duplicate protection for mutations. Do not treat a login endpoint as a business operation or pass arbitrary paths from the frontend.

Configure `settings.integrations.traffic_suite` with `{"auth_mode":"user"}`. `required:true` gates on the app grant, not an IDaaS/session readiness check; optional user-mode consent may still appear at entry. On a failed request, give a local retry and guide the visitor to the relevant consent, Relay action, portal permission, or later retry. Test the actual operation with the intended visitor; a successful login is insufficient.
## Quick examples

- `traffic_suite.get("/tracking-gateway/tms-user-service/api/login")`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
