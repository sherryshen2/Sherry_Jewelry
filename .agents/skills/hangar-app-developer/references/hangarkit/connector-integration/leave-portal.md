# Leave Portal

ID: `connector_integration.leave_portal`
Category: `connector_integration`

Use the fixed Sea leave portal with current-user browser access and privacy-aware workflow handling.

## Import

`from hangarkit.integrations import leave_portal`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `leave_portal.call(operation_id, *, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`
- `leave_portal.request(method, path, *, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`

## Details

Read the shared Relay concept and portal contract before designing setup. Leave Portal uses each visitor's grant and website account at fixed `https://leaveapp.sea.com`. There are no `env` or `region` selectors and no owner mode or `ensure_access`. A valid cached session may work while Relay is offline.

Connector supplies the site session and cookie-derived `X-CSRFToken`. The app must not read cookies, ask for passwords, or generate that header. An HTML leave-summary page is not proof that a particular leave submission or manager action is authorized.

Search/describe `provider="leave_portal"` and inspect the actual contract, maturity, and confirmation requirements. Keep employee identifiers, dates, and approval scope validated in authenticated backend actions. Leave records are private; expose only necessary fields. Obtain explicit reviewed confirmation for submission/cancellation/approval mutations and do not retry them blindly after uncertain outcomes. Use the common HTTP/error contract and feature-local consent, sign-in, denial, and retry states.
## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
