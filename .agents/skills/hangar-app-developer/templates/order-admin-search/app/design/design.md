# Order Search Design

This file is durable project memory for Hangar Agent. Keep it aligned with the current product requirements, UI, and user experience.

## User Requirements
- Preserve explicit user requirements and corrections across sessions.
- Build the smallest complete product that satisfies the latest user request.
- Keep the Order Admin integration in App User mode (`auth_mode: 'user'`), not App Owner mode. Each app user supplies their own Connector grant, website session, and Relay; do not change this mode unless explicitly requested.

## Product Decisions
- This is a private, read-only Order Admin search workspace. The app uses `order_admin` in App User mode (`auth_mode: 'user'`); each user grants Connector access for this app and uses their own website session.
- The user chooses environment and region before a single explicit `ensure_access` check. A `ready` result unlocks search for that target even if Relay is offline with a valid cached session. Changing the target invalidates the visible ready state.
- Connector consent, website access, local Relay setup, and the actual order-list request are separate steps. Never claim order search works from a grant or an access check alone.
- The app uses the documented `query-order-list-with-filters` catalog operation, with server-side field validation and bounded pagination. Blank search browses the latest orders after access succeeds; neither Order ID nor SN nor another filter is required. A numeric primary key tries Order ID first and then Order SN only if the ID has no match. Never show synthetic orders.

## Experience Principles
- Make the first screen immediately useful for the app's primary workflow.
- Prefer clear, compact controls over decorative explanation.
- Keep empty, loading, error, and success states visible and helpful.
- Preserve accessibility basics: semantic controls, readable contrast, touch-friendly targets, and responsive layouts.

## Visual System
- Use a restrained palette with meaningful contrast; avoid one-note color themes.
- Use 8px-or-less card radius unless the user asks for a softer brand style.
- Use consistent spacing, icon sizing, typography scale, and button hierarchy.
- Put reusable colors, fonts, radius, shadows, and spacing into Design fields when app code references CSS variables.

## Layout Notes
- Mobile-first layout with stable dimensions for repeated UI elements.
- Keep primary actions easy to reach and secondary actions visually quieter.
- Avoid nested cards and marketing-style hero layouts unless the app explicitly needs them.

## Component Notes
- The access panel is compact and target-specific. Recovery copy uses `state` and `next_action.actor`, never a guessed local CLI state. Expandable setup instructions link to the official Connector CLI guide only when session recovery needs Relay.
- Step 1 shows a visible spinner while checking access and a neutral connecting state for pending user-session work. Keep retries explicit, prevent duplicate checks, and direct owner-mode recovery to the owner. Confirmed access ends step 1's loading state before the initial order search starts; order loading belongs to step 2. Status icons respect reduced-motion preferences.
- The primary search fields are optional Order ID/SN, seller username, buyer username, and shop ID. Advanced filters cover checkout ID, cross-border, backend/frontend status IDs, payment method ID, courier, purchased date range, and status-updated date range. Clear filters returns to the latest-order view. Browser-local dates become inclusive Unix-second ranges before sending to the backend.
- Results show payment method and checkout ID, courier and fulfilment channel ID, statuses, cross-border, and purchased/updated times with clear empty/error/pagination states. No payment-method ID is returned by the documented response, so do not fabricate one.

## Implementation Guardrails
- Use HangarKit app-local helpers for runtime routes, assets, data, and backend calls.
- Do not hardcode project IDs or routes to another app.
- Do not store secrets, credentials, one-off status updates, or transient chat notes in this file.
