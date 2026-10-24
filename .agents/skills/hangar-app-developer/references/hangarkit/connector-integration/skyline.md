# Skyline

ID: `connector_integration.skyline`
Category: `connector_integration`

Build against Skyline's fixed digital-QA test host and verify APIs independently of a successful portal sign-in.

## Import

`from hangarkit.integrations import skyline`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `skyline.call(operation_id, *, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, full_response=False, preview=False)`
- `skyline.request(method, path, *, env=None, region=None, params=None, json=None, data=None, headers=None, timeout=30, auth_mode=None, full_response=False)`
- `skyline.get(path, **kwargs)`
- `skyline.post(path, **kwargs)`

## Details

## Identity and site

Skyline is a standalone current-user Craft integration for `digital-qa.test.shopee.io`. It is a **fixed test host**, not an arbitrary Skyline environment selector. Do not pass `env` or `region`: HangarKit rejects both. Connector checks the visitor's app grant; Relay may obtain their portal session through the site's login flow (which can involve `space.shopee.io`). The app must never handle cookies or passwords. Read `connector_integration.relay` to explain this to an unfamiliar user and offer setup only when needed. An existing session can work with Relay offline. Owner mode and HangarKit `ensure_access` are unavailable; `call` works when an operation is cataloged.

The portal kit probes `/api/auth/me`. This can establish that the selected account is signed in, not that a Skyline business operation is permitted. Do not send users to another environment by changing a URL or adding an unsupported `env` flag.

## Establish the API contract

Connector has a `skyline` Relay integration entry but **no bundled Skyline operations** at present. Confirm the active catalog through Craft's app-scoped search with `provider="skyline"` or `connector api search --service skyline <task>`. If a reviewed operation is later added, prefer `skyline.call(operation_id, ...)`. Otherwise, before implementing `skyline.request(...)`, get and check an independent maintained contract for method, relative path, required input, permission, and risk. See `relay_portals` for full response and safe preview. Keep the fixed operation in an authenticated backend action with validated inputs, not a general-purpose proxy. The `me` example is a session probe only.

Configure `settings.integrations.skyline` as `{"auth_mode":"user"}`; `required:true` is a grant-only entry rule. Optional current-user consent may still be shown before the app. On failure, offer feature-local retry, distinguish consent from site denial and Relay/session recovery, and avoid asserting that CLI installation is missing from a server error. Verify the real API as the intended visitor on the fixed test host before calling the feature complete.
## Quick examples

- `skyline.get("/api/auth/me")`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
