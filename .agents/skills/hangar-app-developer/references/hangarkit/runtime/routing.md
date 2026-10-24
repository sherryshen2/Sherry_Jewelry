# Single-domain app routing

ID: `runtime.routing`
Category: `runtime`

Public apps are served by path, not custom domain: {host}{HANGAR_APP_PREFIX}/apps/:slug.

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `{prefix}/apps/:slug`
- `{prefix}/apps/:slug/api/*`
- `{prefix}/apps/:slug/data/*`
- `{prefix}/apps/:slug/assets/*`
- `{prefix}/apps/:slug/realtime`

## Details

All generated app links, backend calls, assets, data, and realtime routes must be app-scoped and prefix-safe.

Production users and agents enter through `https://wingman.shopee.io/hangar`.
VM addresses and upstream prefixes are internal; never switch clients to them
to work around routing or authentication failures. App-development agents use
`/api/external/hangar/*` beneath the public base with their Wingman bearer token;
browser management routes use Hangar sessions. Neither path bypasses app
permissions. Upstream permission, rate-limit, and service failures keep their
HTTP status and safe message rather than being reported as invalid credentials.
Agent preflights use `/api/external/hangar/slug-availability` and
`/api/external/hangar/spaces` on that same public base. Slug changes check every
VM before writing once to the owner; Space assignments are checked on the
owning/creation VM. Neither check requires browser cookies.

Frontend code should use `nav.href()` and `nav.localPath()` for routes. Backend code should use `app_url()`, `api_url()`, and `asset_url()` for URLs.

Checks and publishing compile a browser-mounted frontend without server rendering. Static template thumbnails still use server rendering, so prefer `onMount`, `$effect`, or event handlers for browser-only work. For routes and query params, use `nav.localPath()` so code works under `{prefix}/apps/:slug`. A successful compile does not verify browser execution or third-party CDN availability.

Published browser bundles preserve component styles for every route. Route components may keep their styles colocated with their Svelte files.

Runtime requests and scheduled jobs reuse published source in a bounded,
process-local cache keyed by app and release. Access rules, ownership, secrets,
and integration choices still come from the current project metadata under the
existing lookup policy; they are never taken from cached release settings.
Saves invalidate that app's slug lookups, including old and new slugs on rename,
without clearing other apps' lookups. Publishing or rolling back selects the
corresponding immutable source; ordinary draft saves do not replace live code.
Legacy published apps remain supported without a new migration.

Runtime app access requires a signed-in Hangar user except for configured public backend API endpoints. Public apps can be opened by any signed-in user. Private apps can be opened by owners, editors, listed members, platform admins, and users whose Wingman `department_full_path` prefix-matches an explicitly configured `settings.permissions.departments` path. Department paths are slash-separated hierarchy paths stored as `string[][]`; selected parent departments include child departments, and each selected path segment is matched as a prefix, so allowed `abc` matches actor department `abcdef` but not `abzdef`. Normal catalog users only receive apps they can open. Catalog department filtering is an admin-only tool and uses both top-level owner `team` metadata and explicit `settings.permissions.departments`; top-level `team` does not grant private access by itself. Platform admins receive owner/editor-equivalent runtime grants for app data and realtime snapshots.

Explicit team editing uses `settings.permissions.editor_departments`, a subset
of allowed `departments`. It grants the same editor privileges as email editing
with case-insensitive whole-segment hierarchy matching, including subteams;
legacy use-only grants never acquire editing implicitly. See `runtime.sharing`.

Backend callback routes can be made reachable without Hangar login by adding exact entries to `settings.public_endpoints`. Public endpoint URLs use `{host}{HANGAR_APP_PREFIX}/apps/:slug/api/*`. For SeaTalk, prefer the platform callback route `{host}{HANGAR_APP_PREFIX}/api/callback/seatalk/:slug`, which acknowledges non-verification callbacks before forwarding them to the app backend. Public endpoints only apply to backend API routes; data, asset, cache, integration, and cross-app routes stay protected. Backend code must verify provider signatures or shared secrets before trusting public callback payloads.

Do not reintroduce custom-domain or per-domain routing behavior.

Sharing is controlled only by `settings.visibility`: Private, Unlisted, or
Public. Unlisted allows signed-in access by link but is excluded from ordinary
catalog discovery. Saved coherent edits apply automatically without changing
sharing. See `runtime.sharing` for update/recovery and backward compatibility.
## Related capabilities

- `frontend.hangarkit`
- `backend.hangarkit`
- `runtime.sharing`
