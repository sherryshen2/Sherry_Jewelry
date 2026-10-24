# SeaTalk Open Platform

ID: `connector_integration.seatalk_open`
Category: `connector_integration`

Use the browser-backed SeaTalk Open developer portal, distinct from messaging and app-credential APIs.

## Import

`from hangarkit.integrations import seatalk_open`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `seatalk_open.call(operation_id, *, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, full_response=False, preview=False)`
- `seatalk_open.request(method, path, *, env=None, region=None, params=None, json=None, data=None, headers=None, timeout=30, auth_mode=None, full_response=False)`
- `seatalk_open.get(path, **kwargs)`
- `seatalk_open.post(path, **kwargs)`

## Details

## Which SeaTalk integration is this?

`seatalk_open` connects to the **browser-authenticated developer portal** at `open.seatalk.io`, not the separate HangarKit `seatalk` messaging integration or an app-bot credential. Each app visitor uses their **own** Connector grant and portal account. Relay may refresh that person's website session if necessary, but a cached session can work with Relay offline. Read `connector_integration.relay` for plain-language consent, Relay setup, and recovery. No owner mode, service credential, or `ensure_access` exists here; catalog-backed `call` is supported.

The upstream host is fixed; do **not** pass `env` or `region`. The SDK rejects both. `/api/auth/v2/me` is the portal's reviewed session/current-user probe; portal sign-in is not proof that the person may administer a particular company or app.

## Discover and call carefully

Search/describe `provider="seatalk_open"` in Craft's app-scoped catalog (or use `connector api search/describe --service seatalk-open`) for exact method, relative path, body, company/app identifiers, maturity, risk, and confirmation. The catalog includes bundle and app-management operations, some destructive. Prefer `seatalk_open.call(operation_id, ...)` for a **verified**, server-owned operation in an authenticated backend route; use `request` only for independently verified uncataloged endpoints. See `relay_portals` for full response and safe preview. Validate company/app scope and never accept arbitrary proxy paths or unconfirmed writes from a visitor. The example `me` request only demonstrates the session.

Set `settings.integrations.seatalk_open` to `{"auth_mode":"user"}`. `required:true` checks the grant, not the company permission or browser session; optional current-user integrations may still prompt for consent at entry. When the operation fails, present a scoped retry and distinguish missing consent, session work, permission denial, and uncertain write outcome. Follow the shared Relay page for action-required jobs rather than opening a browser by default. Verify the real operation with the intended portal user and permitted app/company.
## Quick examples

- `seatalk_open.get("/api/auth/v2/me")`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
