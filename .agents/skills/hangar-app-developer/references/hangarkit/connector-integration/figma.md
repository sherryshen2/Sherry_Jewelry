# Figma

ID: `connector_integration.figma`
Category: `connector_integration`

Call reviewed Figma APIs with Connector-managed OAuth access rather than browser Relay or pasted credentials.

## Import

`from hangarkit.integrations import figma`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `figma.request(method, path, *, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`
- `figma.call(operation_id, *, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`

## Details

Read `connector_integration.native_apis` for user/owner selection, consent, responses, and errors. Figma uses the selected person's linked OAuth credential; Connector owns token injection and its upstream refresh behavior. The configured Figma API base defaults to `https://api.figma.com`. Do not pass `env`, `region`, or `domain_id`; Hangar apps cannot choose arbitrary Figma hosts. No browser Relay worker is required.

Figma currently has a native proxy but no bundled operation catalog entry. Check the active app-scoped catalog before using `call`; do not invent IDs if it is empty. For a reviewed Figma API contract, use relative `/v1/...` paths through an authenticated backend `request`, with validated file keys and inputs. `/v1/me` only verifies identity; it does not establish access to every file, team, comment, or write.

Explain whose Figma account the app uses. An app grant does not bypass Figma file permissions or OAuth scopes. On failure, show local retry or linked-account recovery, not Relay installation instructions. Review response data before exposing it to visitors, particularly in owner mode.
## Quick examples

- `figma.get("/v1/me")`

## Related capabilities

- `connector_integration.native_apis`
