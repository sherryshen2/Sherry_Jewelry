# Seller SOP

ID: `connector_integration.seller_sop`
Category: `connector_integration`

Use regional Seller SOP browser access, distinct from native Seller Portal Open APIs.

## Import

`from hangarkit.integrations import seller_sop`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `seller_sop.call(operation_id, *, env, region, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`
- `seller_sop.request(method, path, *, env, region, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`

## Details

Read both shared Relay pages first. `seller_sop` is a browser-backed Seller SOP portal using each visitor's grant and website session; it is not the token-based `seller_portal` Open API integration. No owner mode or `ensure_access` exists here. Cached portal access may work with Relay offline.

Pass `env` and `region` on every SDK call. Environments: `live`, `uat`, `test`, `staging`, `stable`. Regions: `br`, `cn`, `id`, `my`, `ph`, `sg`, `th`, `tw`, `vn`. Vietnamese hosts start with `banhang`; the other supported markets use `seller`. Stable uses `test-stable.`. Do not offer the larger Order Admin/CS region set or interpret CN as TWS's separate CN route.

Discover `provider="seller_sop"` operations in Hangar's catalog and inspect maturity, seller/resource inputs, method, body, and risk. Prefer catalog-backed `call`; use `request` only for independently verified contracts. Keep server-owned actions and reviewed marketplace choices, obtain explicit confirmation for mutations, and avoid returning private seller information unnecessarily. Follow the shared error contract and scoped consent/session/permission recovery. A successful login is not proof of permission for a seller action.
## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
- `connector_integration.seller_portal`
