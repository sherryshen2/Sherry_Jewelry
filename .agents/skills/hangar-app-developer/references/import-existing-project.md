# Import Existing Project Checklist

Use this checklist when adapting an existing app or repository into a Hangar app. The goal is not to copy files blindly; the goal is to remap identity, API calls, storage, assets, secrets, and deployment to Hangar/HangarKit conventions.

## First Pass Inventory

- Identify the frontend entrypoint and convert it into `frontend/src/App.svelte`.
- Identify server routes and convert them into `backend/main.py` using FastAPI.
- List all environment variables, API keys, OAuth/client credentials, and webhook secrets.
- List all persistent stores: localStorage, IndexedDB, browser cookies, SQLite, Postgres, Redis, file writes, object storage, and third-party databases.
- List all HTTP clients and route assumptions: absolute URLs, `/api` base paths, project IDs, tenant IDs, and cross-app calls.
- List all auth/session assumptions: app-owned login, JWT parsing, OAuth callbacks, user profile endpoints, role checks, and logout behavior.
- List UI customization systems: theme providers, CSS variables, design tokens, i18n files, CMS/content config, local preferences, feature flags, white-label branding, and hardcoded copy/media.
- List generated or uploaded files and decide whether each becomes a Hangar asset, table record, or backend temporary file.

## Identity and Login

Prefer Hangar/Wingman identity over app-owned authentication. Hangar app users are always required to log in through Hangar before using the app shell or app backend routes, so HangarKit auth should be the default user identity layer.

- Frontend: use `auth.currentUser()` or `auth.requireUser()` from `$hangarkit`.
- Backend: use `ctx.user`, `ctx.user_email`, and request metadata from `hangarkit.ctx`. Use `ctx.current_user` (or `ctx.user_name` / `ctx.user_avatar_url`) when the app needs the signed-in user's display profile, including avatar.
- If the imported app has login/register/logout/session screens, ask the user to confirm whether to remove them and migrate identity to HangarKit auth.
- Remove imported login pages unless the user explicitly confirms the app truly needs a second product-specific auth system.
- Do not store independent user sessions in localStorage/cookies for Hangar runtime access.
- Map old roles to Hangar app permissions, custom roles, table access policies, or app table fields.
- If the old app has per-user data, decide whether tables should be `scope: "user"` or `scope: "app"` with explicit owner fields.

Questions to answer:

- Who can open the app: all logged-in Hangar users, only configured members, or editors/admins?
- Does the app need user-specific records, team-shared records, or both?
- Are previous users/owners represented by email, numeric IDs, usernames, or external account IDs?
- Should imported login be removed and replaced with HangarKit auth?

If the user chooses to keep imported OAuth or a second product-specific login:

- Keep Hangar login as the outer runtime identity; treat the imported login as provider/product authorization inside the app.
- Store OAuth client secrets outside source files, in app settings/integration configuration.
- Register provider redirect/callback URLs from `GET /apps/:id` metadata, not from a custom domain.
- Backend OAuth callback: `${api_base_url}/oauth/callback`, for example `{host}{HANGAR_APP_PREFIX}/apps/:slug/api/oauth/callback`.
- Frontend OAuth callback: `${app_url}/oauth/callback`, for example `{host}{HANGAR_APP_PREFIX}/apps/:slug/oauth/callback`.
- If the imported app uses a custom callback path such as `/auth/callback/google`, append that same path to `api_base_url` or `app_url`.
- Project slugs are mutable; if the slug changes, update the provider callback allowlist.

## API Calls and Routing

Hangar runtime traffic is path-based and app-scoped:

```txt
{host}{HANGAR_APP_PREFIX}/apps/:slug
{host}{HANGAR_APP_PREFIX}/apps/:slug/api/*
{host}{HANGAR_APP_PREFIX}/apps/:slug/data/*
{host}{HANGAR_APP_PREFIX}/apps/:slug/assets/*
```

Frontend migration:

- Replace direct calls to local backend paths with `api.get`, `api.post`, etc. from `$hangarkit`.
- Replace hardcoded asset URLs with `asset("filename")`.
- Replace external browser fetches that need proxying with `proxy`.
- Remove hardcoded project IDs, app IDs, tenant IDs, `/hangar/apps/:slug`, and hostnames from frontend code.
- Avoid calling another app's data, assets, or API routes from this app.

Backend migration:

- Put Python routes in `backend/main.py` and export `router = APIRouter()` or `app = FastAPI()/ASGI`.
- Use `app_url()` and `asset_url()` for links returned by backend routes.
- Read request/app/user context from `ctx`, not from custom headers unless needed for imported protocol compatibility.
- If the old backend has multiple services, start with one FastAPI router and split helper modules under `backend/` only after the routes are working.

## UI, Content, Design, and Theme

Refactor UI so it uses Hangar-native runtime helpers and editable surfaces where they matter.

Content mapping:

- Move user-facing copy that non-technical users may edit into `$content`: app title, section headings, button labels, empty states, helper text, onboarding text, footer text, and static product descriptions.
- Move editable media into `$content` or Hangar assets: logos, hero images, product images, background images, downloadable files, and icons that business users may replace.
- Keep code-only strings in source when they are internal state labels, route names, developer diagnostics, or implementation constants.

Design and theme mapping:

- Convert imported design tokens and CSS custom properties into `$design` fields and `var(--token-name, fallback)` usage.
- Create design fields for colors, font families, spacing scale, radii, shadows, chart colors, and component density when those values are intended to be adjusted after import.
- Preserve app-specific visual identity, but align controls, spacing, and responsive behavior with Hangar runtime constraints and accessibility expectations.
- Use HangarKit `theme` helpers for light/dark or platform-driven theme behavior. Do not keep an imported global theme provider unless the user explicitly wants a second product-specific theme system.

Preferences and localization:

- Use HangarKit `preferences` for runtime user preferences such as selected view, density, dismissed tips, and display options.
- Use HangarKit `language` for language-aware UI where applicable.
- If the imported app has i18n files, decide whether strings become `$content` fields, app table records, or remain bundled source translations.

Questions to answer:

- Which text and images should business users be able to edit without code changes?
- Which visual tokens should be exposed as design controls?
- Should imported theme/provider/i18n/preference systems be removed, simplified, or preserved?
- Does the UI still work under `{host}{HANGAR_APP_PREFIX}/apps/:slug` without hardcoded asset or route paths?

## Storage and Data Tables

Prefer Hangar app tables for persistent application data.

- Frontend table CRUD: use `table("name")` from `$hangarkit`.
- Backend table CRUD: use `table("name")` from `hangarkit`.
- Create schemas through app `data` during app creation or through `PATCH /tables/:table`. The old `PUT` replacement returns 410; insert rows explicitly with `POST /tables/:table/record-batches`.
- Use `scope: "app"` for shared team/application data.
- Use `scope: "user"` for private per-runtime-user records.
- Do not persist app data in arbitrary files inside the backend runtime directory; runtime files may be recreated during deployment.

Migration mapping examples:

- `localStorage` preferences -> Hangar `preferences` if UI-level, or a user-scoped table if app-specific.
- SQLite/Postgres table -> Hangar table schema and records.
- Uploaded documents/images -> Hangar assets if files are served directly, or table records with asset filenames if they need metadata.
- Cache-only data -> Hangar cache or backend memory if it is safe to lose.

## Secrets and Integrations

- Never hardcode imported API keys, tokens, app secrets, webhook secrets, or database passwords in files.
- Store runtime secrets in app settings (`settings.services.secrets.variables`) or provider integration settings.
- Use Hangar integrations where available instead of copying app-owned OAuth token storage.
- Backend imports from `hangarkit.integrations` may be detected by Craft. Connector-backed providers default to user auth when no saved provider config exists. Patch a merged `settings.integrations[provider]` config when the import needs app-level auth, service credentials, provider credentials, or quotas.
- For app-provided integrations, keep provider credentials in `settings.integrations[provider]` with `auth_mode: "app"`.
- For user-provided integrations, rely on linked Wingman user accounts where Hangar supports them.
- For imported Google Sheets apps, decide explicitly between user auth and app auth. User auth requires the runtime request to carry the user's normal Wingman JWT; a Hangar session cookie alone is not enough for Sheets. If all users should read a shared owner-controlled sheet, configure `google_sheets` with `auth_mode: "app"` and `app_provider: "owner_token"`; Hangar derives the Wingman owner email from the app owner.
- When migrating raw Google Sheets HTTP calls, prefer `hangarkit.integrations.google_sheets` helper methods. Raw Sheets calls should use `/v4/spreadsheets/...` or `https://sheets.googleapis.com/v4/spreadsheets/...`, not generic Google connector paths.

## Assets and Files

- Keep source files under the virtual filesystem paths Hangar expects.
- Upload binary/static files through `/assets`; reference them with `asset()` or `asset_url()`.
- Do not use build-time paths like `/public/...`, `/static/...`, or absolute local filesystem paths in runtime code.
- If an imported app writes files at runtime, decide whether those writes become table records, assets, or temporary backend files.
- If an imported backend receives uploads over HTTP and the file should remain available later, persist it as a Hangar asset and store the asset filename in a table or domain record. Do not treat a temporary backend filesystem path as durable application state.
- Frontend `$data` file fields automatically upload browser `File` values into app assets. Backend `table(...).create()` and `update()` are JSON-only, so backend-owned uploads need an explicit asset persistence step.

## Backend Runtime

- Include `fastapi` and `uvicorn` in `backend/requirements.txt`.
- Add any imported Python dependencies explicitly.
- Avoid background daemons, long-running side processes, or local cron assumptions unless Hangar runtime explicitly supports them.
- Treat the backend filesystem as deployment/runtime workspace, not durable storage.
- Add a simple `/health` route before importing complex backend logic.
- If the imported app exposes long-running work through HTTP, convert it into a submit/poll task pattern and keep the request path responsive while the work runs.

Minimal backend health route:

```python
from fastapi import APIRouter
from hangarkit import ctx

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "app": ctx.app_slug, "user": ctx.user_email}
```

## Import Validation Checklist

Before publishing:

- No hardcoded project IDs, app IDs, local hostnames, or old deployment URLs remain.
- Frontend uses `$hangarkit` helpers for API, data, assets, auth, preferences, and proxy needs.
- User-editable copy/media and themeable visual tokens have been mapped to `$content`, assets, `$design`, preferences, or app tables as appropriate.
- Backend uses `hangarkit.ctx`, `table`, `app_url`, and `asset_url` where applicable.
- `backend/requirements.txt` contains all Python dependencies, including `fastapi` and `uvicorn`.
- Existing auth has been removed or intentionally isolated from Hangar runtime auth.
- Persistent data has been mapped to Hangar tables, assets, or integrations.
- Secrets have been moved out of files and into settings/integrations.
- Every imported provider integration that needs app-level auth, service credentials, provider credentials, or quotas has an explicit `settings.integrations[provider]` entry.
- App permissions and table scopes match the old product's privacy expectations.
- A `/health` backend route works after publish.
- The app shell and backend routes are verified with a Hangar browser-session cookie.

## Import Strategy

For complex apps, import in layers:

1. Static frontend shell with no persistence.
2. Backend `/health` route.
3. One migrated data table.
4. One migrated API route.
5. Assets/uploads.
6. Auth/role mapping.
7. Remaining integrations and advanced workflows.

Sync and verify each meaningful layer rather than migrating the whole project
at once. Saved changes remain drafts. Publish only when requested, after any
active editing turn finishes. Preserve `settings.visibility` unless the user
requests a sharing change; do not write legacy catalog flags or describe a
Private app as disabled.
