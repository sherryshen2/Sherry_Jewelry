# Python backend integrations

ID: `backend.integrations`
Category: `backend`

Backend integration packages under hangarkit.integrations for connector-backed services, Relay portals, SeaTalk, Wingman Chat, and LLM Chat.

## Import

`from hangarkit.integrations import abtest, confluence, datasuite, google, google_calendar, google_docs, google_drive, google_mail, google_sheets, jira, llm_chat, log_platform, order_admin, pmp, pop, seatalk, space, wingman_chat`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `provider.client()`
- `provider.request(method, path, **kwargs)`
- `provider-specific helper methods`

## Details

Use `hangarkit.integrations` from backend code for privileged or connector-backed provider calls that should not run in the browser.

Supported package names currently exposed by HangarKit include the standard connector integrations, platform helpers, and the Relay portal integrations documented in `connector_integration.relay_portals`.

The new native modules are `gitlab`, `figma`, `notion`, `grafana`, `sea_transify`, `seller_portal`, and `smart`. Read `connector_integration.native_apis` and the named provider page before using them. They support user or owner Connector grants, not pasted service credentials, and never fall back to Wingman, even before owner cutover. Their catalog calls share the Relay modules' full-response/error contract without requiring Relay setup. GitLab alone accepts a configured `domain_id`; Google Sites is instead a separate Relay job integration with page/asset start-and-poll helpers.

Important for local development: integration modules are injected by Hangar with the backend runtime. They are not expected to import in a normal local Python environment.

Integration availability and auth mode depend on the app's Hangar integration settings and platform connector configuration. Backend imports can be detected by Craft. Standard non-Relay Connector providers default to app owner-token auth when no saved provider config exists. All Relay-backed portal integrations default to App User mode (`auth_mode: "user"`), including template setup and detected backend imports. Legacy owner-token migration must not switch Relay integrations to owner mode. Preserve explicitly saved auth choices; only Order Admin supports an explicit owner-token opt-in. Save `settings.integrations` entries when the app needs explicit auth, required access, service credentials, provider-specific credentials, or quotas.

Use a saved config such as `{ "auth_mode": "user" }` for explicit user-linked connector auth, `{ "auth_mode": "app", "app_provider": "owner_token" }` for app owner-token proxy auth, provider-specific app credentials for integrations such as SeaTalk, or `{ "monthly_cost_quota": 10 }` for local quota-managed helpers such as `llm_chat`. Hangar derives the Wingman owner email from the app owner for owner-token mode where applicable.

When Connector OAuth is configured, user auth mode asks each runtime user to authorize the app's supported current-user integrations in Connector with one grant per app/user. The general consent flow can prompt at app entry even for an optional user-mode provider; do not promise that optional means no entry prompt. Order Admin can be marked `required` to explicitly require its Connector grant at entry, not Relay/device/site-session readiness; app workflows check the actual selected target on demand. Owner-token mode for standard providers continues to use the app owner's Wingman access until the actual app owner explicitly connects owner integrations from Craft > Integrations. Order Admin owner mode requires Connector and has no Wingman fallback. Editors and platform admins cannot opt in for the owner. After a successful owner cutover, revoked or invalid Connector access requires reconnection; Hangar does not silently fall back to Wingman.

Published app pages also expose one direct authorize, reconnect, or re-authorize key button in Hangar's injected top bar, separate from the account menu's general Connectors link. There is no authorization submenu. For the actual app owner with owner-account integrations, the button opens owner consent, including any current-user integrations in the same app grant. Other users authorize only their own configured integrations; owners of current-user-only apps use that same user flow. Consent returns to the current app page. Re-authorizing does not remove the existing grant before successful approval; cancelling leaves it unchanged. Provider account linking and Relay website readiness remain separate.

When Connector OAuth is unavailable or the provider is not supported there, existing Wingman user-token approval remains in effect. Hangar's browser/session cookie identifies the runtime user for app access; raw credentials are stored server-side and never exposed to app frontend or backend code.

For owner-token calls routed to Connector, Hangar automatically sends the authenticated runtime actor's normalized email as `X-Connector-Caller-Identifier` only when that actor is not the app owner. Email comparison ignores case and surrounding whitespace. Calls made by the owner omit the identifier because the owner's grant already identifies them. Connector stores any supplied identifier as the optional `caller_identifier` in its proxy audit record; the grant and upstream credentials remain the app owner's. Hangar derives the actor email from a validated runtime user token, never from an app-supplied email or caller-identifier header. App code cannot override this attribution. Background, cron, public callback, or other calls without a validated runtime user omit the identifier rather than pretending the owner triggered them. Current-user mode continues to identify the user through their own Connector grant, and legacy Wingman routing is unchanged. This is audit metadata only, not extra authorization or a verified identity claim made by Connector.

When a frontend-triggered backend request successfully uses a current user's linked integration permission, Hangar briefly pulses the runtime integration bubble so the user can see which connected provider was used.

Prefer the named helper methods when available; use `request()` only for provider endpoints that do not yet have a helper.

For AI calls, choose deliberately: use `wingman_chat.start()` and `wingman_chat.get_run()` for a managed Wingman session with built-in tools (persist its completed `session_id` yourself and do not configure its model or tools); use `llm_chat.chat_completions.create()` for a stateless, raw OpenAI-compatible request where your app defines and executes tool calls.
## Quick examples

- `from hangarkit.integrations import jira`
- `issue = jira.get_issue("ABC-123")`

## Related capabilities

- `backend.hangarkit`
- `backend.integration.jira`
- `backend.integration.log_platform`
- `backend.integration.google`
- `backend.integration.google_drive`
- `backend.integration.google_mail`
- `backend.integration.space`
- `connector_integration.relay_portals`
- `connector_integration.order_admin`
- `connector_integration.native_apis`
