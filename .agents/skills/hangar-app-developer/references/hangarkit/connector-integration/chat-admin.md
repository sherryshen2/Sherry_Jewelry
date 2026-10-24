# Chat Admin

ID: `connector_integration.chat_admin`
Category: `connector_integration`

Expose Chat Admin's environment-scoped Connector APIs while reporting the current Relay CLI support limitation honestly.

## Import

`from hangarkit.integrations import chat_admin`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `chat_admin.call(operation_id, *, env, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`
- `chat_admin.request(method, path, *, env, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`

## Details

Read the two shared Relay pages first. Chat Admin uses the visitor's app grant and browser-backed admin session. It is distinct from HangarKit SeaTalk, Wingman Chat, and LLM Chat. No owner mode or `ensure_access` is exposed.

Connector's backend requires `env` (`live`, `test`, `uat`, `staging`, `stable`) and rejects unsupported environments. HangarKit requires that value and rejects `region`. Hosts are `admin.chat.<env-prefix>shopee.io`; stable aliases staging. Business market fields, if any, are operation inputs.

Important rollout limitation: the checked Connector CLI implementation does not yet list or resolve the `chat_admin` Relay site, even though Connector exposes its proxy and catalog. An existing valid cached session may work, but fresh local session capture cannot be assumed. If recovery needs this site, request a compatible Connector CLI/backend release or support; do not invent a working `connector relay` target, promise installation alone fixes it, or claim this app has been verified.

Search/describe `provider="chat_admin"` and implement only a reviewed fixed operation through the backend. Follow catalog confirmation, bounded inputs, and the shared error/full-response contract. Provide a feature-level unavailable/retry state and support request ID for the CLI limitation. Verify actual API access and recovery on a compatible deployment before release.
## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
