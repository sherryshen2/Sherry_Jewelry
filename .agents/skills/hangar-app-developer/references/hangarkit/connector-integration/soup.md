# SOUP

ID: `connector_integration.soup`
Category: `connector_integration`

Use environment-scoped SOUP portal APIs without treating them as a cookie-export or universal login API.

## Import

`from hangarkit.integrations import soup`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `soup.call(operation_id, *, env, path_params=None, params=None, json=None, data=None, headers=None, confirm=False, timeout=30, full_response=False, preview=False)`
- `soup.request(method, path, *, env, params=None, json=None, data=None, headers=None, timeout=30, full_response=False)`

## Details

Read `connector_integration.relay` and `relay_portals`. SOUP is a standalone current-user portal integration. The visitor needs an app grant and permission for the intended SOUP API. Its SSO session may also help Connector establish other supported portal sessions, but that does not make an app a universal sign-in or credential-export client. Never request cookies or return authentication material to the frontend.

Pass `env` explicitly: `live`, `uat`, or `test`. Do not pass `region`; the host is `soup.<env-prefix>shopee.io`. Staging/stable are unsupported. There is no owner mode or `ensure_access`. Cached access may work offline; a missing session uses the selected user's normal Relay recovery.

Search/describe `provider="soup"` for an exact reviewed operation. Catalog actions can include approval, role, and security workflows; discovered metadata is not an authorization test. Use `call` for verified contracts, keep operation IDs and validated resource scope server-owned, and obtain explicit confirmation for risky actions. Use the common full-response/exception handling and scoped recovery rather than invoking login or approval workflows speculatively.
## Related capabilities

- `connector_integration.relay`
- `connector_integration.relay_portals`
