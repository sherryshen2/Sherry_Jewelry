# Order Admin

ID: `connector_integration.order_admin`
Category: `connector_integration`

Build Order Admin workflows with cataloged operations, Connector grants, and target-scoped Relay recovery.

## Import

`from hangarkit.integrations import order_admin`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `order_admin.ensure_access(*, env, region, timeout=60)`
- `order_admin.call(operation_id, *, env, region, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`
- `order_admin.request(method, path, *, env, region, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`

## Details

## Explain the integration

Order Admin is a standalone integration in Craft, not a generic "Connector integration" card. Read `connector_integration.relay` first for a plain-language explanation of Connector consent, local Relay setup, cached sessions, user-facing copy, and the app-building workflow. Read `connector_integration.relay_portals` for the shared catalog, request, and error contract. This page adds Order Admin's `env`/`region` target, owner mode, and exact `ensure_access` response. Explain the distinction between the app grant and target access before asking anyone to install Relay.

Set `settings.integrations.order_admin` to `{"auth_mode":"user"}` for each app user's grant and Relay (the default), or `{"auth_mode":"app","app_provider":"owner_token"}` for the app owner's grant and Relay shared by app users. Owner mode is not a service token and has **no Wingman fallback**. The owner must complete Connector consent; visitors cannot connect or repair the owner's Relay. Explain the shared owner-account access before selecting this mode. Other Relay portal integrations remain current-user only.

## Discover and call operations

Search and describe operations with Hangar's authenticated `GET /api/external/hangar/apps/:id/integrations/order_admin/operations?q=...` and `GET .../operations/:operation_id` endpoints (see the Integration API Catalog in `references/external-api.md`). Discovery is development-time work; do not put catalog searches in an app's runtime workflow. Catalog access uses the relevant app-scoped Connector grant; until that grant exists, the API returns an authorization-required error. Catalog results include maturity, risk, confirmation requirements, path and input shape. Do not treat `discovered` operations as verified contracts.

`call` resolves the catalog operation internally on every invocation, validates service, method, path parameters, required query and business headers, fixed catalog values, and content type, then routes through Hangar's backend-only proxy to Connector. It rejects unsupported upstream selectors and does not accept a caller-chosen method or arbitrary URL. For `confirmation: required`, obtain the user's confirmation before passing `confirm=True`; this is not an authorization bypass. For endpoints not cataloged or with unsupported shapes, use `request` only after independently verifying the endpoint and risk. `search_operations` and `describe_operation` are also available in backend code, but prefer the developer catalog API for design-time discovery. `full_response=True` returns status, filtered response headers, body encoding/body, and diagnostics **only on HTTP 2xx**; non-2xx raises `order_admin.RelayPortalError` with `exc.response` and `exc.stage`. `preview=True` resolves the catalog without sending the portal request and returns a redacted request outline (path template and field names, not values). Read `relay_portals` for the complete exception-handling example and common contract. Never send credentials, device IDs, cookies, or raw Connector tokens to the app frontend.

Treat the catalog's response schema as a guide, then exercise the operation against a real target. For example, `query-order-list-with-filters` can return `{"has_more": false}` with no `order_list` for an empty result; normalize an omitted list to `[]` rather than reporting an error. Preserve 64-bit order and checkout IDs as strings in browser-facing responses so JavaScript does not round them. A successful `ensure_access` only checks target access; it does not verify the operation's response shape or business permission.

For an Order List-style app, `query-order-list-with-filters` accepts a bounded browse request with just `limit` and `offset`; do not require Order ID/SN or another filter. The portal's search fields map to `order_id` or `order_sn`, `checkout_id`, `cross_border`, `seller_name`, `shop_id`, `buyer_name`, `be_status`, `fe_status`, `payment_method`, `courier`, `ctime_gte/lte`, and `mtime_gte/lte`. A combined ID/SN input may try numeric `order_id` first and retry `order_sn` only if no result; preserve the original string for the retry. Send `cross_border: false` when the user selects No, not as an omitted filter. Date bounds are Unix seconds; if the UI uses calendar dates, convert them in the user's intended timezone and make the upper day inclusive, then validate start <= end. Keep result pages bounded and avoid inventing label-to-ID mappings for status or payment filters. The documented result has a payment-method name but no payment-method ID.

## Choose the entry rule

To require a Connector grant before opening the app, configure:

```json
{
  "auth_mode": "user",
  "required": true
}
```

`required` is a grant-only entry rule. It does not assert that Relay is online or that all environments and regions work. In owner mode, the app owner must connect the grant; app visitors cannot grant on the owner's behalf. Legacy `required_targets` settings are ignored. The general current-user Connector consent gate can still prompt at app entry for a configured or imported user-mode provider even when `required` is false. Do not describe optional as a guarantee that visitors can skip consent in the current gateway.

Leave `required` off when the app has useful features without Order Admin, but test the actual entry behavior if it must open without Connector consent; current-user integrations can still trigger the general consent page. Even when required, do not add a global Relay/session gate: app entry checks the grant; target readiness belongs in the workflow using that target. When user mode is required, each visitor grants the app; when owner mode is required, the owner grants it and visitors wait for the owner. A saved grant can later be revoked, so runtime code must still handle access failure.

## Check the selected target

For a workflow that needs Order Admin, use its selected `env` and `region`. The actual operation is the final proof that *that operation* works. If a dedicated "Check access" control or preflight is useful, call `ensure_access(env=..., region=...)` in an authenticated backend route. This check can validate cached access, mint from SOUP, or queue Relay work; it is not a passive probe and should not run continuously on every render or for all env/region pairs. It returns `state`, `mode`, optional `reason`, and diagnostics:

- `state`: `ready`, `pending`, `relay_offline`, `denied`, `grant_missing`, or `unavailable`; `mode`: `user` or `app`. Use `state` and `next_action` for recovery rather than assuming `reason` is a stable user-facing string.
- `target: {env, region}` and `access: {verified, proof}`. `proof` is `order_admin_auth_info`, `connector_site_auth`, or `none`; verified target access is not a guarantee that every operation is authorized.
- `session: {state, source, verified, expires_at?}` for the selected target. `state` is `active`, `expired`, `invalid`, `needs_login`, `missing`, or `unknown`. `source` is `relay_local_capture`, `soup_mint`, or `unknown`. `verified` is `true` only when an active stored session coincides with proven access; otherwise it is `null`. Missing/unknown metadata does not negate an independently verified access result. No cookie values or headers are returned.
- `relay: {pairing, connection}` for the selected Connector subject (the owner in app mode, current user in user mode). Pairing is `paired`, `not_paired`, or `unknown`; connection is `online`, `offline`, or `unknown`. The response does not expose a device ID or name.
- `local_cli: {installed: "unknown", connected: "unknown", reason: "not_observable_from_hangar_server"}`. These are always `unknown`: Hangar cannot inspect a visitor's Mac. Even an online paired Relay is not evidence that CLI is installed on this particular machine.
- `next_action: {code, actor} | null` with `actor` of `user` or `owner`. Codes include `connect_grant`, `pair_relay`, `start_relay`, `check_relay_setup`, `complete_sign_in`, `complete_relay_task`, `request_access`, `update_relay_policy`, `contact_owner`, `check_target`, and `retry`. In owner mode, app visitors cannot complete the owner's recovery.

For example, a working cached session can coexist with an offline Relay:

```json
{
  "state": "ready",
  "mode": "user",
  "reason": "cookie_cached",
  "target": {"env": "live", "region": "sg"},
  "access": {"verified": true, "proof": "order_admin_auth_info"},
  "session": {"state": "active", "source": "soup_mint", "verified": true},
  "relay": {"pairing": "paired", "connection": "offline"},
  "local_cli": {
    "installed": "unknown",
    "connected": "unknown",
    "reason": "not_observable_from_hangar_server"
  },
  "next_action": null
}
```

`ready` is target-specific and temporary. The access check proves Order Admin auth-info or Connector site auth, not the specific business operation. A cached session can work with Relay offline; diagnostic lookups are best-effort, so `unknown` means unverified, not absent. Do not override `ready` because a diagnostic says `offline`, `missing`, or `unknown`. A returned `denied`/`pending`/`relay_offline` state is a **normal result of a successful access-check HTTP call**, not an exception; a non-2xx or transport failure raises `RelayPortalError` (`stage="access"`, `response` present only for HTTP failure).

## Build the app workflow

Keep Connector calls in the backend. For example, in an authenticated FastAPI router (included from `backend/main.py`), expose a check scoped to the user's selected target:

```python
from fastapi import APIRouter
from pydantic import BaseModel
from hangarkit.integrations import order_admin

router = APIRouter()

class Target(BaseModel):
    env: str
    region: str

@router.post("/order-admin/access")
def check_order_admin_access(target: Target):
    return order_admin.ensure_access(env=target.env, region=target.region)
```

The frontend calls `api.post('/order-admin/access', {env, region})` after target selection or a user-triggered retry, shows the returned `target` and a concise status, and offers a retry control. Put the real `order_admin.call(...)` behind a separate authenticated backend action with server-side validation of the requested operation/inputs. Do not accept arbitrary catalog IDs, HTTP paths, or `confirm=True` from an untrusted UI. Catch both access-check transport errors and actual-operation failures; a previous `ready` is not a permanent entitlement.

Map state and action to a recovery panel in the affected workflow:

| Result | What the app should explain and offer |
| --- | --- |
| `ready` | Continue with the intended operation; show Relay diagnostics only as optional detail, not a blocker. |
| `grant_missing` / `connect_grant` | Current user completes this app's Connector consent in user mode. In owner mode, direct them to the owner; the owner uses Craft > Integrations or the owner authorization handoff. |
| `pending` / `complete_sign_in` or `complete_relay_task` | Relay may still be working in the background. Offer a retry after a short wait; ask the `next_action.actor` to inspect Connector Relay actions and continue a job only if one is actually reported. A `soup_sign_in_required` reason can become `ready` without manual sign-in. Do not open a browser preemptively. |
| `relay_offline` / `pair_relay`, `start_relay`, or `check_relay_setup` | The selected actor checks Connector CLI installation and local Relay status on their computer, pairs or starts the background service if needed, then retries. Do not equate the server's paired-device state with this visitor's installation. |
| `denied` / `check_target`, `request_access`, `update_relay_policy`, or `contact_owner` | Correct the target, request Order Admin permission, ask the selected actor to resolve Relay policy, or contact the app owner, according to the code. Do not keep retrying a denial without a change. |
| `unavailable` / `retry` | Explain that readiness could not be verified; retry later, and surface a support path if persistent. Do not mislabel it as a missing local CLI. |

For local setup and pending-job instructions, use the shared `connector_integration.relay` page. Do not ask for cookies or assume Hangar can install Connector CLI or open the Relay browser on a visitor's computer.

Tell a visitor in owner mode "The app owner needs to restore Order Admin access for this target," not "Install Relay on your computer." Keep working features available while this target is recovering. A feature that cannot function without Order Admin may disable its own submit action until checked, with a visible retry; do not hide the rest of the app.

## Verify an app

Test the actual published runtime with separate owner and visitor identities as appropriate. Verify required versus optional entry and report any optional user-mode consent prompt, current-user versus owner subject, at least two env/region pairs, a valid cached session with Relay offline, an expired/missing session with pending sign-in, unpaired/offline Relay, denied permission, and Connector outage. In owner mode, confirm that a visitor sees owner-directed recovery and cannot authorize on the owner's behalf. Exercise the real read or write operation after `ready`, including confirmation for a risky write, and recheck after a session expires. A green frontend build, Connector grant, catalog search, browser sign-in, or `ensure_access` result by itself is not end-to-end proof.
## Quick examples

- `access = order_admin.ensure_access(env="live", region="sg")`
- `result = order_admin.call("retrieve-current-authenticated-user-info", env="live", region="sg")`

## Related capabilities

- `backend.integrations`
- `connector_integration.relay`
- `connector_integration.relay_portals`
