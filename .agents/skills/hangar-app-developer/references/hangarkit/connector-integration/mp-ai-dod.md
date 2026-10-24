# MP AI DOD

ID: `connector_integration.mp_ai_dod`
Category: `connector_integration`

Call the fixed staging AI DOD portal with current-user access and reviewed operation contracts.

## Import

`from hangarkit.integrations import mp_ai_dod`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `mp_ai_dod.call(operation_id, *, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`
- `mp_ai_dod.request(method, path, *, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`

## Details

Read both shared Relay pages first. MP AI DOD uses the current user's Connector grant and site session on fixed `https://aidod.staging.shopee.io`. It is not a selectable live/test/staging integration. The SDK rejects `env` and `region`. No owner mode or `ensure_access` is provided. Cached access may work with Relay offline.

The portal's permission probe is `/api/admin/v1/okr_dashboard/check_permission`; it is not proof that another admin, query, image, or streaming operation is authorized. Connector owns session capture and cookies. Explain consent separately from the person's portal permission.

Search/describe `provider="mp_ai_dod"` and inspect request media type, input/body, risk, and output type. Use `call` for a verified operation or `request` for an independently verified uncataloged contract. A response need not be JSON: `full_response=True` represents non-UTF-8 binary as base64. Bound query/body sizes and display content safely. Provide a scoped retry/recovery state and verify the actual operation as the intended user on this staging host.
## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
