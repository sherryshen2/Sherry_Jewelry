# GitLab

ID: `connector_integration.gitlab`
Category: `connector_integration`

Use GitLab APIs with an app-scoped Connector grant and optional configured GitLab target selection.

## Import

`from hangarkit.integrations import gitlab`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `gitlab.call(operation_id, *, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, domain_id=None, full_response=False, preview=False)`
- `gitlab.request(method, path, *, params=None, json=None, data=None, headers=None, timeout=30, domain_id=None, full_response=False)`

## Details

Read `connector_integration.native_apis` first. GitLab is a standalone native integration, not a Relay site. Connector uses a linked OAuth account on a configured GitLab host. No local CLI/Relay installation is required just to use the app. Choose current-user or owner access explicitly; the Hangar default is the owner's account. App consent does not expand the GitLab account's original OAuth scope or project membership.

Do not pass `env` or `region`. Without `domain_id`, Connector selects the linked/default configured target and may reject ambiguous accounts. With `domain_id`, HangarKit uses Connector's `/targets/gitlab/:domain_id` route. Supply a configured target ID, never an arbitrary hostname, URL, or invented production/test flag. That target must have the selected person's linked account. Server-allowlist any target choices exposed by the app.

The shared SDK rejects encoded path separators as well as slash-bearing path parameters. Catalog operations requiring those shapes (for example some repository-file paths) need a reviewed SDK routing extension before use; an entry in the catalog is not a guarantee every shape is supported. Do not work around this by exposing arbitrary URLs to the frontend.

Search/describe `provider="gitlab"` in Hangar's catalog, then use `gitlab.call` for a verified operation. For independently verified uncataloged endpoints, use a relative `/api/v4/...` path with `request`. Prefer numeric project/group IDs; the SDK rejects slash-bearing path parameters rather than guessing how to encode a namespace. Validate resource scope on the backend. Mutations need reviewed intent and permissions, not merely a successful `/api/v4/user` probe.

`full_response`, preview, and `ConnectorError` follow the shared native contract. Recover a missing app grant separately from an expired or missing linked GitLab account. In owner mode, direct account recovery to the owner. Test the actual operation against every target the app offers.
## Quick examples

- `gitlab.get("/api/v4/user")`

## Related capabilities

- `connector_integration.native_apis`
