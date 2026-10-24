# Notion

ID: `connector_integration.notion`
Category: `connector_integration`

Use versioned Notion API contracts while Connector manages linked OAuth or token authentication.

## Import

`from hangarkit.integrations import notion`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `notion.request(method, path, *, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`
- `notion.call(operation_id, *, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`

## Details

Read `connector_integration.native_apis` first. Notion is a native linked-account API, not a Relay site. Connector supplies the saved OAuth or token credential and owns its supported OAuth refresh. The app supplies the reviewed API version, request fields, and resource identifiers. There are no HangarKit `env`, `region`, or `domain_id` selectors.

Connector forwards `Notion-Version`; it does not choose a version for the app. Use the version required by the maintained upstream contract and ensure the payload matches it. Do not interchange database and data-source endpoints or invent a version from older examples. Authentication headers and cookies are Connector-owned.

No bundled Notion operation catalog currently exists. Search the active catalog, but use `notion.request` for independently verified relative `/v1/...` contracts when no operation is available. Validate page/database/data-source scope in the backend; an integration account can only access shared/authorized resources. Never offer an unrestricted Notion proxy or generic destructive action.

Choose the user's or owner's account through the app settings and explain the access boundary. `ConnectorError.response` contains HTTP details when available; filter them before frontend use. For account recovery, ask the selected person to reconnect Notion in Connector, not install Relay. Verify real reads and any writes as the intended account.
## Related capabilities

- `connector_integration.native_apis`
