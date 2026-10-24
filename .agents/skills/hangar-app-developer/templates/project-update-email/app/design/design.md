# __HANGAR_APP_NAME__ Design

This file is durable project memory for Hangar Agent. Keep it aligned with the current product requirements, UI, and user experience.

## User Requirements
- Preserve explicit user requirements and corrections across sessions.
- Build the smallest complete product that satisfies the latest user request.

## Product Decisions
- Add durable product, data, permission, integration, and workflow decisions here.

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
- Add durable component decisions here, such as navigation style, table density, form patterns, modal behavior, and chart conventions.

## Implementation Guardrails
- Use HangarKit app-local helpers for runtime routes, assets, data, and backend calls.
- Do not hardcode project IDs or routes to another app.
- Do not store secrets, credentials, one-off status updates, or transient chat notes in this file.
