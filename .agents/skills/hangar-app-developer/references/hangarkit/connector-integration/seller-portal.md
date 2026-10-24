# Seller Portal

ID: `connector_integration.seller_portal`
Category: `connector_integration`

Use native Seller Portal Open APIs without confusing them with the browser-backed Seller SOP portal.

## Import

`from hangarkit.integrations import seller_portal`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `seller_portal.request(method, path, *, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`
- `seller_portal.call(operation_id, *, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`

## Details

Read `connector_integration.native_apis` first. `seller_portal` uses a linked token for Seller Portal Open APIs, whose configured server base defaults to `https://seller-portal.i.shopee.io`. It is not `seller_sop`, which is a regional browser-backed portal. Do not ask Seller Portal API users to install Relay or add `env`/`region` selectors; the SDK rejects those and `domain_id`.

The native proxy exists but no bundled Seller Portal operation catalog is currently available. Search the active catalog first; use `seller_portal.request` only with an independently maintained, verified upstream contract when it is empty. Confirm exact path, body, seller/resource identifiers, and risk. Do not infer Open API endpoints from Seller SOP website paths.

Connector owns credential headers and account validation. Choose current-user or owner access, explain borrowed owner permission, and constrain backend actions to reviewed resources. The shared error/full-response contract applies; account expiry requires the selected person's linked-account recovery, not repeated app consent or browser Relay setup. Verify the actual read/write permission before release.
## Related capabilities

- `connector_integration.native_apis`
- `connector_integration.seller_sop`
