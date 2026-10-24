# Connector and Browser Relay

ID: `connector_integration.relay`
Category: `connector_integration`

Explain browser-backed integrations to first-time app builders and users, and design their setup and recovery flow.

## Caller guidance

This page documents a workflow rather than a callable helper. Follow its ordered steps and use the linked capability page before calling a runtime API.

## Details

An app may need to read or change information on a company website such as Order Admin. **Connector** is the service that checks whether the app has permission and carries approved API requests. Some websites require a browser sign-in rather than an ordinary API account. **Browser Relay** is the small Connector background worker on a person's paired computer that can establish or refresh that website session using a separate browser profile. The person signs in only when requested. The app never needs their password or cookies.

An app user should normally experience this as: open the app, approve the app's access when prompted, use the feature, and follow a sign-in prompt only if the selected website needs one. A valid cached session can work even while Relay is offline. Do **not** make everyone install Connector CLI or sign in to every region before they can try the app.

The Connector grant prompt may be a **Hangar page before the app loads**, even when a current-user integration has `required: false`. The app's own target selector and Relay recovery UI cannot replace or appear ahead of that platform consent page. Have the selected person approve the app's named provider there; then test the app's target-specific check. Do not click through a person's grant on their behalf or promise an optional provider will be invisible at entry.

For a **local Hangar** server, the OAuth callback must return to that same local server because it owns the pending grant state and PKCE verifier. Leave `HANGARKIT_CONNECTOR_CALLBACK_URL` unset locally to derive the current request origin, or set it to that exact local callback. Connector's `hangar` registrar must separately allowlist the resulting full URI (including host, port, prefix, and path); Connector permits HTTP loopback but rejects an unlisted redirect. For example, a Hangar server at `http://127.0.0.1:5174/hangar` needs `http://127.0.0.1:5174/hangar/api/auth/connector/callback` in the registrar's exact allowlist. A callback to the deployed test Hangar cannot complete a local app's grant. Connector bootstraps the registrar allowlist into its database only once: editing the service config afterward does not update an existing registrar record. If registration is rejected, ask the Connector registrar administrator to check the **active database allowlist** and the exact URI; do not bypass the redirect check or claim consent succeeded.

Relay is a mechanism, **not** an integration to add in Craft. Configure Order Admin, Promotion Admin, or another supported provider as its own integration. This page is reusable guidance for all browser-backed providers. Read `connector_integration.relay_portals` for shared request constraints and a provider-specific page such as `connector_integration.order_admin` for the actual methods, target inputs, and any readiness response. Do not assume all providers support Order Admin's `ensure_access`.

Google Sites is a distinct Relay workflow: page and asset reads are queued jobs executed by an online local browser, not ordinary HTTP calls using cached cookies. Read `connector_integration.google_sites` before designing that app. Native GitLab, Figma, Notion, Grafana, Sea Transify, Seller Portal, and SMART APIs are documented in `connector_integration.native_apis`; do not give their users Relay installation steps.

## Explain the separate steps

| Question | Plain-language explanation | What to do if it fails |
| --- | --- | --- |
| May this app use the integration? | "Allow this app to use your [service] access." This is an app-specific Connector grant, not a website login. | The selected person completes the Hangar/Connector consent flow. |
| Can the selected person use this website target? | "Check access to [service] in [environment/region]." A grant does not sign them in everywhere. | Try the feature or a documented target check; follow the result. |
| Is fresh browser sign-in needed? | "Connector needs a session for this website." Relay uses the selected person's paired computer and its dedicated browser. | Set up that person's Relay only when needed, then complete a reported sign-in action. |
| Did the requested work succeed? | "The request worked" or an actionable error. A green device status is not proof. | Retry the actual operation after recovery; handle its own errors. |

In current-user mode, each app user supplies their own grant and website access. Some providers also support owner mode; **currently Order Admin** can use the app owner's grant, Relay, and website access for visitors. Decide who should be responsible for the integration with the app owner before building. Do not ask a visitor to install Relay to repair an owner-mode app. Other Relay portal providers are current-user only.

## What the app-building agent should say

Explain the setup without assuming the owner knows the product names: "I can build [feature] using [service]. Connector will ask the right person to allow this app to use that service. If a website sign-in is needed later, the small Relay helper on that person's computer will handle it. You do not need to install it just to start building." Ask who should supply the account only if that provider supports both user and owner mode; also ask for the target environment/region when it changes which APIs the feature uses.

If the API catalog requires a Connector grant, tell the selected person exactly which app and provider they must approve. Continue with honest setup-ready UI and backend structure when possible, but do not invent an operation, claim that it works, or publish a write workflow as verified without the needed contract and real authorization. After building, distinguish "app published" from "grant completed," "website session ready," and "tested with a real request." Give the owner one next action at a time.

## Build the app around it

1. **Choose the provider and job.** Ask what the app must do and which website, environment, and region it uses. Discover documented operations during development; verify inputs and write risk. A browser page or Google sign-in alone does not prove API access. Do not invent an operation or assume every provider has a catalog.
2. **Configure the integration.** Use the provider's standalone `settings.integrations` entry and a supported user/owner mode. Explain whose account will be used. `required: true`, where supported, concerns the Connector grant at app entry, not an always-online Relay or valid sessions for every target. The general current-user consent flow may still prompt on entry for an optional provider; test the actual app.
3. **Keep the request in the backend.** The frontend sends only the intended action and selected target to an authenticated backend route. HangarKit and Connector handle the grant, target, cached session, and Relay work. Never accept arbitrary API paths or privileged operations from untrusted UI, or expose cookies, Connector tokens, or Relay device IDs.
4. **Make failure local and recoverable.** Show the affected feature's status and a retry control, not a whole-app Relay blocker. Do a target check when it helps the user, or simply attempt the real operation. A check may start session work, so do not run it on every render or repeatedly poll without a bound. Recheck the actual operation after recovery; previous success can expire.
5. **Test the user journey.** Use the published app with the identities that will use it. Check grant missing, cached success with Relay offline, missing/expired session, stopped or unpaired Relay, pending sign-in, denied website permission, and successful retry. Test separate env/region pairs where supported. In owner mode, verify that visitor-facing recovery points to the owner.

## Write useful app messages

Use the provider name and target in user-facing copy. Keep internal status codes and CLI details out of the main screen; offer setup steps only when relevant.

| Situation | Example message and action |
| --- | --- |
| Grant missing | "Connect [service] to use this feature." Offer the app's Connector consent action; in owner mode, say "The app owner needs to connect [service]." |
| Working | Show the result. Do not warn merely because Relay is offline if the request succeeded. |
| Session work pending | "Connector is preparing access to [service] in [target]. Check again shortly. If Connector asks for sign-in, finish that action on your paired computer." Show **Try again**. |
| Relay unavailable and no usable session | "Connector can't reach your Relay right now. Check setup on your computer, then try again." In owner mode, replace "your" with "the app owner's" and give a contact path. |
| Website access denied | "Your account does not have access to [service] in [target]. Request website access or choose another target." Do not suggest repeated login if permission is denied. |
| Connector unavailable or unclear | "We couldn't check [service] right now. Try again later." Do not claim the CLI is missing without local evidence. |

These are examples, not a universal error schema. Map the actual provider's documented response or error to a safe message. Order Admin's `ensure_access` has `state`, `next_action.actor`, and diagnostics; other providers may only report errors from the real request. Keep an explicit loading/pending state and allow retry after the person completes recovery.

## When local Relay is actually needed

Offer the selected person the [official Connector CLI download and setup guide](https://connector.shopee.io/docs/cli). On their own computer, they sign in with `connector login`, check `connector relay status --local`, pair with `connector relay pair` if needed, and install or restart the managed background worker with `connector relay service install`. These are local steps; Hangar cannot install software or inspect CLI installation on a visitor's computer. Pairing a computer does not sign in to every website target.

When a request reports pending session work, Relay may first try the existing browser profile in the background; `pending` alone does **not** prove that a person must sign in. Let the person retry the app after a short wait. If Connector asks for user action, they inspect `connector relay actions list` and continue **only the reported job** with `connector relay actions continue --job <job-id>`. If the list says no action requires confirmation, do not invent a job or open a browser; wait for background work and retry. They sign in inside the dedicated Relay browser only when prompted. Do not use `connector relay run` as normal setup. Never ask for passwords, exported cookies, or browser-profile files.

Connector may reuse a site-specific cached session or obtain access without a visible browser for supported targets. The device connection describes the selected Connector person's paired worker, not necessarily the visitor's computer. A website session may be scoped by site, environment, and region; selecting a tenant or project in a web UI does not automatically supply API request headers. The actual operation remains the final proof of access.
## Related capabilities

- `connector_integration.relay_portals`
- `connector_integration.order_admin`
