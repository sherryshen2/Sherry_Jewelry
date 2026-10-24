# ShopeeFood Admin

ID: `connector_integration.shopeefood_admin`
Category: `connector_integration`

Use ShopeeFood Admin's own environment/market set and Connector-managed CSRF handling.

## Import

`from hangarkit.integrations import shopeefood_admin`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `shopeefood_admin.call(operation_id, *, env, region, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`
- `shopeefood_admin.request(method, path, *, env, region, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`

## Details

Read the Relay concept and shared portal API pages. This integration uses the current app user's grant and ShopeeFood website permission, not an app owner's shared account. No `ensure_access` exists. Cached access may work while Relay is offline; fresh site sign-in belongs to the selected user.

Require `env` (`test`, `uat`, `staging`, `live`) and `region` (`id`, `my`, `ph`, `th`, `vn`). There is no stable environment and no SG/TW/BR target. Hosts follow `food-admin.<env-prefix>shopee<regional-suffix>`. Connector injects the cookie-derived `X-SF-CSRF-Token`; do not expose or fabricate that value. The permission probe above does not guarantee a specific food order or administration action is allowed.

Search/describe `provider="shopeefood_admin"` before fixing an operation in the backend. Review required inputs, catalog maturity, risk, and confirmation; POST is not enough to classify intent. Use `call` for a verified operation, or `request` for an independently verified uncataloged contract. Apply the common full-response/exception contract and a target-scoped recovery/retry UI. Validate business scope and test the real operation with the intended user and market.
## Quick examples

- `shopeefood_admin.get("/api/auth/permissions", env="test", region="id")`

## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
