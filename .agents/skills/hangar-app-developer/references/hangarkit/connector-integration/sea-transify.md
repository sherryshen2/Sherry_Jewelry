# Sea Transify

ID: `connector_integration.sea_transify`
Category: `connector_integration`

Call project-authorized Sea Transify APIs with a Connector-managed translation credential.

## Import

`from hangarkit.integrations import sea_transify`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `sea_transify.call(operation_id, *, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`
- `sea_transify.request(method, path, *, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`

## Details

Read `connector_integration.native_apis` for account selection and errors. Sea Transify is a native project-token integration. Connector prepends its fixed `https://transify.sea.com/api` base and injects the stored `Authorization: Token ...` credential. Do not paste a token into Hangar files or headers. No Relay, `env`, `region`, or `domain_id` is supported.

Search/describe `provider="sea_transify"` (Connector service `sea-transify`) for the exact contract. Prefer `call` for verified operations; raw `request` uses a path relative to the `/api` base, so do not accidentally duplicate that prefix. Translation project, namespace, language, and key identifiers are operation inputs, not routing flags. Validate their scope and mutation intent on the server.

An app grant does not expand the linked token's project permission. Explain user versus owner access; owner mode shares only the app's fixed actions. Follow the shared full-response and `ConnectorError` handling, and direct missing/expired project credentials to the selected person's Connector account setup rather than Relay installation.
## Related capabilities

- `connector_integration.native_apis`
