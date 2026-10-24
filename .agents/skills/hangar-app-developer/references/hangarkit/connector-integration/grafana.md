# Grafana

ID: `connector_integration.grafana`
Category: `connector_integration`

Use the selected linked Grafana domain and organization without exposing session or service-token material.

## Import

`from hangarkit.integrations import grafana`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `grafana.call(operation_id, *, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`
- `grafana.request(method, path, *, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`

## Details

Read `connector_integration.native_apis` first. Grafana is native linked-account access. Connector selects the account's stored, allowlisted HTTPS Grafana domain (default `https://grafana.shopee.io`) and tries its stored session cookie before its service token. These details remain in Connector; do not ask app visitors to provide them. A stored Grafana session is not Hangar browser Relay.

Do not pass `env`, `region`, or `domain_id`. Changing a dashboard datasource or query's business region is not changing the proxy host. Connector can supply the stored organization context; do not assume a caller-supplied org header expands access. Expose only reviewed dashboard/datasource choices.

Search/describe `provider="grafana"` and prefer `call` for a verified catalog operation. Use `request` only for independently verified uncataloged paths. Query bodies, time windows, datasource IDs, and result sizes require backend validation and bounds. Dashboard access does not imply datasource query or write permission.

Use the shared full-response/error contract. Distinguish missing app consent, invalid linked account, and Grafana permission denial. In owner mode visitors borrow only the app's offered actions, not unrestricted dashboard access; recovery belongs to the owner. Do not show raw response data or session diagnostics indiscriminately.
## Related capabilities

- `connector_integration.native_apis`
