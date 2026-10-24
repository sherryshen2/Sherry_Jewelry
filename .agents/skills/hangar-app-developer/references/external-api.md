# Hangar External API

All endpoints require:

```http
Authorization: Bearer <Wingman token JWT>
Content-Type: application/json
```

Treat the header above as documentation, not an executable command. Before running any request, replace placeholders with real values or environment variables. Never execute commands that still contain placeholders such as `<Wingman token JWT>`, `<app_id>`, `<slug>`, `<path>`, or `<updated>`.

For asset upload, omit JSON content type and send multipart form data.

Set `HANGAR_BASE_URL` to the Hangar host plus any configured prefix:

```bash
export HANGAR_BASE_URL="https://wingman.shopee.io/hangar"
```

This is the production public base for every app, regardless of its hosting VM.
Use `$HANGAR_BASE_URL/api/external/hangar/*` for agent app operations. Do not
switch to VM origins, internal prefixes, or browser `/api/projects` routes
after a failure. The gateway resolves app ownership internally without
requiring browser cookies; the owning Hangar still enforces the caller's access.

Report the returned HTTP status and diagnostic message without credentials.
401 means authentication failed; 403 is a permission denial; 429 is rate
limiting; 5xx indicates a server or upstream-service failure. Identity-service
connection failures return 502 and timeouts return 504. Do not ask the user to
replace their token for a non-authentication failure or retry writes blindly.

In a Toolverse-hosted workspace, use the `WINGMAN_TOKEN` already supplied in
the command environment. If it is missing or rejected with 401, stop and report the
authentication failure. Do not read desktop auth files or copy tokens from chat.

For local development only, prefer an already exported `WINGMAN_TOKEN`;
otherwise read the Wingman auth file and verify it is not expired:

```bash
if [ -z "${WINGMAN_TOKEN:-}" ]; then
  export WINGMAN_TOKEN="$(
    python3 - <<'PY'
import json, pathlib, sys, time

path = pathlib.Path.home() / ".wingman" / "auth.json"
try:
    data = json.loads(path.read_text())
except Exception:
    sys.exit(0)

token = str(data.get("accessToken") or "").strip()
expires_at = int(data.get("expiresAt") or 0)
if token and expires_at > int(time.time()) + 60:
    sys.stdout.write(token)
PY
  )"
fi
```

For local development, if `WINGMAN_TOKEN` is still empty, ask the user to get or refresh one at:

```txt
https://wingman.shopee.io/connectors/token
```

Do not print the token in logs or final answers.

Preflight before the first authenticated request:

```bash
test -n "$HANGAR_BASE_URL" && test -n "$WINGMAN_TOKEN" && [ "$WINGMAN_TOKEN" != "<token>" ]
```

## Public Skill Version

These endpoints are public and do not require `Authorization`. Agents should call them before using the installed `hangar-app-developer` skill so they can self-update when the hosted skill is newer.

### Check latest skill version

```bash
curl -sS "$HANGAR_BASE_URL/api/skills/hangar-app-developer/version"
```

Response:

```json
{
  "skill": {
    "name": "hangar-app-developer",
    "version": "2026.10.13.1",
    "updated_at": "2026-10-13T00:00:00.000Z",
    "latest_file_updated_at": "...",
    "sha256": "...",
    "file_count": 5,
    "total_bytes": 12345,
    "compatibility": { "min_codex": "0.0.0" }
  },
  "version_url": "https://wingman.shopee.io/hangar/api/skills/hangar-app-developer/version",
  "download_url": "https://wingman.shopee.io/hangar/api/skills/hangar-app-developer/download"
}
```

### Download latest skill package

```bash
curl -L "$HANGAR_BASE_URL/api/skills/hangar-app-developer/download" -o hangar-app-developer.zip
```

The zip contains a top-level `hangar-app-developer/` folder with `SKILL.md`,
`skill-version.json`, agents, scripts, references, and every app template under
`templates/`. Read `templates/INDEX.md` to choose one without loading them all.
The response includes `X-Hangar-Skill-Version`.

Hosted sessions use `/api/skills/hangar-toolverse-app-developer/version` and
`/api/skills/hangar-toolverse-app-developer/download`. That package has its own
entrypoint and folder name, with the same CLI, references, and templates.

## Caller-Only HangarKit API

Use `GET /kit/catalog` and `POST /kit/call` beneath the external API base to
discover and invoke public SDK methods with the caller's own permission,
without deploying a Python app backend. There is no additional gateway
confirmation flag for writes; effects are real. App-bound methods use
`POST /apps/:id/kit/call`, require app edit access, and keep the caller as actor.
Native/Relay calls need a matching caller Connector token or the caller's app
grant; owner/service credentials are never substituted. Read
[the Kit API contract](hangarkit/runtime/kit-api.md) for discovery, exact call
shapes, binary uploads/output, unsupported runtime-only methods, and limits.

## Sharing And Publishing

Apps use `settings.visibility: "private" | "unlisted" | "public"`.
All require Hangar sign-in. New apps are Private. Unlisted apps are accessible
by link but excluded from ordinary catalog discovery; Public apps are listed.
Owners, editors, allowed private members/departments, and platform admins retain
their existing roles. Visibility changes alone do not grant editor access.
Craft's Publish dialog supports both Email grants and Team grants.
Organization grants use the existing `settings.permissions.departments`, for
example `[["Company", "Engineering"]]`, and default to Can use. Match the
authenticated Wingman department hierarchy, not email domains; existing
case-insensitive per-segment prefix and child-department matching is unchanged.
A root path such as `[["Company"]]` covers the whole matching organization.
For explicit Can edit, include the same allowed path in
`settings.permissions.editor_departments`, for example
`{"settings":{"permissions":{"departments":[["Company","Engineering"]],"editor_departments":[["Company","Engineering"]]}}}`.
Editing uses whole-segment hierarchy matching, not legacy partial-name matching:
subteams qualify, but `Engineering Operations` does not match `Engineering`.
Team editors have the same privileges as email editors, including settings and
sharing, but cannot become owners or delete the app. Missing editor paths mean
no team editing. Clear `editor_departments` to downgrade all teams to use-only;
removing a path from `departments` also removes its editor grant. Partial
unrelated settings/permission writes preserve existing editor grants.
Use `{"settings":{"permissions":{"departments":[]}}}` to clear organization
grants without removing individual people. Keep visibility Private for an
org-restricted audience; Public/Unlisted still allow other signed-in users.

Use `PATCH /apps/:id` with `{"settings":{"visibility":"unlisted"}}`.
Settings are merged at the top level; merge nested integration objects before
replacing those objects. `permissions` is merged with locked ownership.
The compatibility `catalog_enabled` and `permissions.access` fields are derived.
Legacy-only patches still work: public access plus catalog on maps to Public;
catalog off maps to Unlisted; private access maps to Private. A catalog-only
patch cannot open a Private app. Explicit visibility takes precedence.
Opening existing apps or changing only sharing never releases old drafts.
Saved source changes remain drafts until explicit publishing. Submit coherent
files/content/design together in one patch. The bundled CLI push batches file
changes into one request. Separate file requests are independent saves.
Summary responses include `visibility` and `delivery` (`status`, `error`,
`warning`). Do not patch server-owned release or delivery metadata.

`POST /apps/:id/publish` explicitly publishes the saved draft, never an
audience change. Wait for active editing turns to finish before publishing.
`superseded: true` means no release was activated. Read back status and verify a
fresh app page rather than equating a saved edit with a completed release.

Preview code and test records are isolated from the published app. Table
definitions, secrets, assets, and external effects are shared.
See [sharing and publishing](hangarkit/runtime/sharing.md).

## Template Setup

Templates let an external agent discover starter apps and create a complete Hangar app without hand-building the initial virtual filesystem.

### List templates

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/templates" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

Response:

```json
{
  "default_template_id": "craft-starter",
  "templates": [
    {
      "id": "seatalk-bot",
      "name": "SeaTalk bot",
      "description": "A private SeaTalk assistant...",
      "icon": "mdi:robot-happy-outline",
      "tags": ["SeaTalk", "Bot", "Webhook", "Python"],
      "setup": {
        "title": "SeaTalk bot setup",
        "steps": [
          {
            "id": "credentials",
            "title": "SeaTalk credentials",
            "fields": [
              {
                "id": "seatalk_app_id",
                "label": "SeaTalk app ID",
                "type": "text",
                "required": true,
                "integration": { "provider": "seatalk", "key": "app_id" }
              }
            ]
          }
        ]
      }
    }
  ]
}
```

Setup field definitions are instructions for app creation. Fields with `integration` are stored in `settings.integrations`, fields with `secret` are stored under app secrets, and fields with `metadata` are stored under `settings.template_metadata`. The API never returns submitted secret values.

The SMART workflow runner's administrator-managed SMART Project schema importer is an in-product onboarding control. It is not exposed through this external API; callers provide normalized template setup values directly and must never send or request the administrator's SMART service-account token.

App secrets live under:

```json
{
  "settings": {
    "services": {
      "secrets": {
        "variables": [
          { "key": "OPENAI_API_KEY", "value": "..." }
        ]
      }
    }
  }
}
```

Important behavior:

- Secret variable names use `key`, not `name`.
- Reads redact secret values. Depending on the surface, secret reads may come back as `[redacted]` placeholders or as an empty `variables` array.
- Do not interpret an empty returned `variables` array as proof that no secrets are configured.
- When changing other settings, read-merge-patch the full `settings` object so unrelated secret configuration is preserved.

### Get one template

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/templates/seatalk-bot" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

Response:

```json
{ "template": { "id": "seatalk-bot", "name": "SeaTalk bot", "setup": { "steps": [] } } }
```

### Render a template payload

Use render when an agent needs to inspect generated files, data tables, Content, Design, settings, or the composed template prompt before creating the app.

```bash
curl -sS -X POST "$HANGAR_BASE_URL/api/external/hangar/templates/craft-starter/render" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Starter App","slug":"starter-app"}'
```

Response:

```json
{
  "template": { "id": "craft-starter", "name": "Craft starter" },
  "slug": "starter-app",
  "payload": {
    "files": [{ "path": "frontend/src/App.svelte", "content": "..." }],
    "content": [],
    "design": [],
    "data": {},
    "storage": {},
    "settings": {},
    "initial_prompt": "Use this generated Hangar app as the starting point..."
  }
}
```

For templates with required setup fields, include `setup_values` or `template_setup_values` in the render body. Do not put setup secrets in URL query strings.

## App Metadata

### Check a slug and list Spaces

These read-only endpoints use the same bearer authentication as app operations:

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/slug-availability?slug=team-dashboard" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
curl -sS "$HANGAR_BASE_URL/api/external/hangar/spaces" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

Slug availability returns `{"slug":"team-dashboard","available":true}` after
normalizing the input. It does not return another app's identity or reserve the
slug. Through the public gateway, every VM is checked and an incomplete check
fails closed. Saving a slug still performs collision checks before the owner
write, including when the requested slug is already this app's slug.

Spaces returns an array of the existing Space records. The gateway merges
matching definitions and rejects conflicting definitions. An app may reference
only Space IDs present on its owning VM (or the creation VM for a new app).
Sending `spaces: []` clears assignments; omitting it leaves them unchanged.
Space administration remains separate and requires platform-admin access.
Do not use browser `/api/projects/slug-availability` or `/api/spaces` for agents.

### List manageable apps

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

The list endpoint returns compact app metadata by default and is safe for agents to call before they know an app id. It supports pagination, search, slug lookup, updated filtering, and an allowlist of simple metadata fields:

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps?limit=25&q=todo&fields=id,name,slug,updated,app_url" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

Response:

```json
{
  "apps": [
    {
      "id": "...",
      "name": "...",
      "slug": "...",
      "app_url": "...",
      "preview_url": "...",
      "catalog_thumbnail_url": "...",
      "updated": "...",
      "revision": "..."
    }
  ],
  "page": 1,
  "perPage": 25,
  "totalItems": 1,
  "totalPages": 1,
  "hasMore": false,
  "view": "summary"
}
```

Query parameters:

- `page` / `perPage` or `limit`: paginate manageable apps. `perPage` is capped at 100.
- `q`: search by id, name, slug, or space id.
- `slug`: exact slug match.
- `ownership=owned`: return only apps whose owner id or normalized owner email matches the authenticated user. Editor access and platform-admin visibility do not count as ownership.
- `updated_after`: ISO timestamp; returns apps updated after that time.
- `fields`: comma-separated allowlist for simple metadata. Supported fields are `id`, `name`, `slug`, `spaces`, `preview_url`, `app_url`, `api_base_url`, `data_base_url`, `assets_base_url`, `catalog_thumbnail_url`, `catalog_enabled`, `app_icon`, `project_title`, `file_count`, `asset_count`, `content_count`, `design_count`, `created`, `updated`, and `revision`.
- `view=full` or `fields=full`: opt into full app metadata for the current page only. Avoid this unless the agent truly needs files/settings/content/design in the list response.

Only apps the token user can manage are returned: owner/editor apps, plus all apps for platform admins. Public catalog visibility alone does not make an app appear in this developer API.
For an inexpensive ownership check, request `?ownership=owned&limit=1&fields=id` and test whether the returned `apps` array is non-empty.
Published app thumbnails are returned as authenticated platform URLs in `catalog_thumbnail_url` and mirrored in `settings.catalog_thumbnail` for compatibility. Fetch these URLs with the same Hangar session cookie or `Authorization: Bearer $WINGMAN_TOKEN`; clients should not expect inline base64 thumbnail data.
On first publish, Hangar generates a catalog launcher badge from the app name when `settings.catalog_badge` is missing. The badge is stored as a data URL in `settings.catalog_badge` with `settings.catalog_badge_updated_at`. Craft no longer exposes icon/backdrop editors or an app icon in its header; existing image metadata remains available to legacy catalog and runtime consumers.

### Create an app

To start from a template, send `template_id` and optional setup answers. Hangar computes the final unique slug before rendering the template, so generated callback URLs and metadata use the same slug as the created app.

```bash
curl -sS -X POST "$HANGAR_BASE_URL/api/external/hangar/apps" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Team Bot",
    "slug": "team-bot",
    "template_id": "seatalk-bot",
    "setup_values": {
      "seatalk_app_id": "123456",
      "seatalk_app_secret": "...",
      "seatalk_callback_signature": "..."
    },
    "settings": { "visibility": "private" }
  }'
```

`settings` is shallow-merged over the template settings. Explicit `files`, `content`, `design`, `data`, or `storage` fields override the corresponding template payload fields. Template/custom `data` entries that look like Hangar table dumps are materialized into app tables during creation, including their schema, scope, icon, access policy, and seed records. The create response includes normal app metadata plus `template_initial_prompt` when the template provided a composed starter prompt for the agent.

Create requests always assign ownership to the authenticated token user. Ownership cannot be changed through the external API, Craft, or agent tools. Only a Hangar platform admin can transfer ownership through the dedicated admin operation.

To create an app from fully custom files instead:

```bash
curl -sS -X POST "$HANGAR_BASE_URL/api/external/hangar/apps" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d @app-create.json
```

`app-create.json`:

```json
{
  "name": "Codex Todo",
  "slug": "codex-todo",
  "spaces": [],
  "settings": { "visibility": "private" },
  "content": [
    { "name": "Hero Title", "type": "text", "value": "Hello Hangar", "description": "Main page title" },
    { "name": "Empty Message", "type": "text", "value": "No items yet", "description": "Shown when the list is empty" }
  ],
  "design": [
    { "name": "Accent Color", "css_var": "--accent-color", "type": "color", "value": "#2563eb" },
    { "name": "Card Radius", "css_var": "--card-radius", "type": "radius", "value": "8px" }
  ],
  "files": [
    {
      "path": "frontend/src/App.svelte",
      "type": "file",
      "language": "svelte",
      "content": "<script>import content from '$content'</script><main><h1>{content.hero_title}</h1><p>{content.empty_message}</p></main><style>main{font-family:system-ui,sans-serif;padding:2rem;color:var(--accent-color,#2563eb)}h1{border-radius:var(--card-radius,8px)}</style>"
    },
    {
      "path": "backend/main.py",
      "type": "file",
      "language": "python",
      "content": "from fastapi import APIRouter\n\nrouter = APIRouter()\n\n@router.get('/health')\ndef health():\n    return {'ok': True}\n"
    },
    {
      "path": "backend/requirements.txt",
      "type": "file",
      "language": "text",
      "content": "fastapi\nuvicorn\n"
    }
  ]
}
```

### View metadata

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

`GET /apps/:id` returns full app metadata by default for backward compatibility, including files, content fields, design fields, settings, `preview_url`, `app_url`, `api_base_url`, `data_base_url`, and `assets_base_url`.

For a compact detail response, request summary fields:

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID?fields=id,name,slug,updated,app_url" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

Sensitive settings values such as tokens, secrets, credentials, passwords, API keys, private keys, and callback signatures are returned as `[redacted]`. When you read-merge-patch settings, passing the `[redacted]` placeholder back preserves the existing saved secret.

For imported apps that keep their own OAuth/login flow, use these returned URLs to configure provider callback allowlists:

- Backend callback: `${api_base_url}/oauth/callback`
- Frontend callback: `${app_url}/oauth/callback`

If the backend callback must be reachable without Hangar login, add the exact backend path to `settings.public_endpoints` and register `${api_base_url}${path}` with the provider. If the app uses a different callback path, append that path to `api_base_url` or `app_url` accordingly. Project slugs are mutable, so update provider allowlists after a slug change.

### Patch metadata or full file list

```bash
curl -sS -X PATCH "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  -H "If-Match: $APP_REVISION" \
  -H "Content-Type: application/json" \
  -d '{"name":"New Name","slug":"new-slug","spaces":[],"settings":{"visibility":"public"}}'
```

Allowed fields: `name`, `slug`, `spaces`, `settings`, `storage`, `custom_instructions`, `files`, `content`, `design`, `data`.

`settings` is merged at the top level, with partial permission patches preserving unspecified permission fields. Send only changed keys. Read and merge nested values such as `settings.integrations` before replacing those objects; unrelated keys inside a replaced nested object can otherwise be dropped.
Ownership fields such as `settings.permissions.owner_id`, `settings.permissions.owner_email`, and legacy owner fields are ignored on ordinary updates and remain unchanged.
To avoid overwriting concurrent Craft or agent edits, fetch the app or its file
manifest and send its opaque `revision` as `If-Match`, or as `revision` /
`if_match` in a mutation body. The API uses the record timestamp when available
and a content-hash fallback for older databases without timestamps. Do not
construct revisions yourself. A mismatch returns HTTP 409; refresh and inspect
concurrent edits before retrying.

Public callback/webhook backend routes are configured under `settings.public_endpoints`:

```json
{
  "settings": {
    "public_endpoints": [
      {
        "id": "post-seatalk-callback",
        "method": "POST",
        "path": "/seatalk/callback",
        "label": "SeaTalk event callback",
        "enabled": true
      }
    ]
  }
}
```

The route exposed publicly is `${api_base_url}${path}`. Public endpoints only apply to backend API routes under `/apps/:slug/api/*`; backend code must verify provider signatures or secrets.

Public endpoint notes:

- Publish first, even for Private apps. These routes execute the published
  release, not Preview or saved drafts; republish handler changes. Login bypass
  does not bypass publication or provider-signature checks. For SeaTalk, prefer
  the [platform callback route](hangarkit/backend/integrations-seatalk.md).
- Matching is exact by method and path.
- Verify the published runtime route directly after publish; a correct external API patch does not by itself prove runtime reachability.
- Some browser-style cross-site `POST` submissions to published runtime routes can be rejected by same-origin protections. For verification or automation against public multipart/form endpoints, prefer a normal HTTP client and send `Origin` / `Referer` matching the Hangar runtime URL when required.

`content` and `design` are replaced by the arrays you send. Read the app first and merge existing fields unless you intentionally want to replace the whole Content or Design tab. Field `id` values are optional for new fields and generated by Hangar when omitted; preserve existing ids when updating existing fields. Use `content` for user-editable text, markdown, booleans, JSON, numbers, and images. Use `design` for CSS variables referenced by app code.

Code and metadata must match:

- A Content field named `Hero Title` is available as `content.hero_title`.
- A Design field with `css_var: "--accent-color"` is available as `var(--accent-color, fallback)`.
- If you add or rename a `content.some_key` reference, patch the Content array in the same change set.
- If you add or rename an editable CSS variable, patch the Design array in the same change set.
- If the user asks to change existing copy or images, update the matching Content field value; changing only code around `content.some_key` will not change the rendered value.
- If the user asks to change an existing theme/color/style token, update the matching Design field value; changing only `var(--token, fallback)` fallbacks will not override Hangar's injected `--token`.

Example content/design patch:

```json
{
  "content": [
    { "name": "Hero Title", "type": "text", "value": "Team tasks", "description": "Main page title" }
  ],
  "design": [
    { "name": "Accent Color", "css_var": "--accent-color", "type": "color", "value": "#2563eb" }
  ]
}
```

Example merged patch using `jq` after reading the app:

```bash
jq '{
  content: (((.app.content // []) | map(select(.name != "Hero Title"))) + [
    { name: "Hero Title", type: "text", value: "Team tasks", description: "Main page title" }
  ]),
  design: (((.app.design // []) | map(select(.css_var != "--accent-color"))) + [
    { name: "Accent Color", css_var: "--accent-color", type: "color", value: "#2563eb" }
  ])
}' /tmp/hangar-app.json > /tmp/hangar-content-design.json

curl -sS -X PATCH "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/hangar-content-design.json
```

## Integration Settings

Backend imports make integrations detectable in Craft. All 24 Relay providers default to current-user access; only Order Admin permits explicit owner mode. The seven new native providers and established standard Connector providers default to owner-token access, preserving saved user choices. New native providers require Connector from the start, with no Wingman fallback; legacy fallback applies only to established standard providers. Platform/local SDKs such as SeaTalk and LLM Chat have their own config rules. Patch merged settings rather than replacing unrelated integration entries. `required:true` concerns the app grant, never live Relay readiness or sessions for all targets. The current gateway can still prompt for current-user consent at entry when optional. Check real provider access inside the affected workflow; only Order Admin has `ensure_access`.

Supported HangarKit backend integration package names:

```txt
Existing SDKs:
abtest, confluence, google, google_calendar, google_docs, google_drive, google_mail, google_sheets, jira, llm_chat, log_platform, pmp, pop, seatalk, space, wingman_chat

Relay SDKs:
order_admin, promotion_admin, cmt_admin, product_label_admin, ssc_ops, user_admin, listing_admin, bd_centre, tws, datasuite, seatalk_open, skyline, traffic_suite, cs_portal, dms_cs_portal, seller_sop, shopeefood_admin, noti_admin, chat_admin, listing_qc_admin, soup, leave_portal, mp_ai_dod, google_sites

New native Connector SDKs:
gitlab, figma, notion, grafana, sea_transify, seller_portal, smart
```

See `references/hangarkit.md` for provider-specific helper methods and auth-mode caveats.

Read the current app:

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  > /tmp/hangar-app.json
```

Configure explicit user-linked connector auth, such as Jira:

```bash
jq '{
  settings: ((.app.settings // {}) |
    .integrations = ((.integrations // {}) + {
      jira: { auth_mode: "user" }
    })
  )
}' /tmp/hangar-app.json > /tmp/hangar-settings.json

curl -sS -X PATCH "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/hangar-settings.json
```

Configure app owner-token mode where supported. Established standard providers may use linked Wingman access before Connector cutover; Order Admin and the seven new native providers require the owner's Connector grant immediately. Relay providers other than Order Admin cannot use owner mode:

```json
{
  "auth_mode": "app",
  "app_provider": "owner_token"
}
```

Do not set `owner_email` for owner-token mode. Hangar derives the Wingman owner email from the app owner.

Configure app service-token mode, where supported helpers call the provider with an app credential:

```json
{
  "auth_mode": "app",
  "app_provider": "service_token",
  "credential": "..."
}
```

Configure SeaTalk bot credentials:

```json
{
  "auth_mode": "app",
  "app_id": "...",
  "app_secret": "...",
  "callback_signature": "..."
}
```

Connector-backed helpers such as `jira` and `pop` default to app-owner permission without a saved integration config. Order Admin is an exception: it defaults to current-user permission. `wingman_chat` defaults to app-owner permission; set `settings.integrations.wingman_chat.auth_mode` to `user` for approved current-user permission.

To remove saved configuration entirely, delete the provider key from `settings.integrations` and patch the merged settings. If backend code still imports the provider, Craft may continue to show the detected integration card and the provider may continue to run with its default auth mode.

### Integration API Catalog

Search the current app's permission-filtered operations during development. The provider segment accepts all 24 standalone Relay providers in the shared `relay-portals` reference and the native keys `gitlab`, `figma`, `notion`, `grafana`, `sea_transify`, `seller_portal`, and `smart`. These endpoints require app edit permission and the relevant app-scoped Connector grant (the owner's grant in supported owner mode, the caller's in user mode):

```bash
curl -sS -G "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/integrations/order_admin/operations" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  --data-urlencode "q=auth"

curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/integrations/order_admin/operations/retrieve-current-authenticated-user-info" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

Replace `order_admin` in those URLs with the chosen provider key. Inspect maturity, risk, confirmation, required path/query/header/body inputs, fixed query/header values, content type, and returned method/path before writing app code. If authorization is missing, have the selected person complete the Connector grant; do not invent endpoints. The running app should prefer `provider.call(operation_id, ...)` through HangarKit for a verified catalog operation, not search the catalog in the frontend. Use `provider.request(method, path, ...)` only for an independently verified uncataloged endpoint. `call(..., preview=True)` resolves and validates the operation without sending it, returning only the method, path template, target, field names, body presence/type, and risk/confirmation; it never returns request values or credentials. `full_response=True` on `call` or `request` returns response status, sanitized headers, body encoding/body, and diagnostics; it is not an outgoing request dump. A catalog entry or preview does not prove that a selected site session or operation is accessible. Read the named `connector-integration` provider page and shared `relay-portals`/`relay` pages for target inputs and recovery.

HangarKit does **not** return an error envelope normally for non-2xx: these modules raise `provider.ConnectorError`, regardless of `full_response` (`RelayPortalError` remains available for Relay modules). In backend code inspect `exc.response["status"]` only when `exc.response is not None`; the envelope includes a capped but potentially sensitive upstream `body`. No response means local validation or a transport failure. `exc.stage` identifies catalog lookup, provider request, Order Admin access check, or validation. The shared Relay and native API references have complete exception examples, including how to read error bodies/headers. Do not expose exception strings or upstream response bodies directly in the frontend.

Read `native-apis` for the new native providers: no Relay installation and no `env`/`region` flags; GitLab alone accepts a configured `domain_id`. Their owner access requires Connector without Wingman fallback. Figma, Notion, and Seller Portal do not currently have bundled operation catalogs, so use independently verified raw contracts instead of invented IDs. Google Sites has local-execution page/asset jobs, not a Google Drive or cached-cookie proxy. Existing non-Relay integrations such as Jira still use their provider-specific helpers; they are not added to this catalog endpoint by these changes.

### Current-User Connector Authorization

For the new native modules, an owner authorization status of `legacy` means owner Connector consent is still needed; it does not enable Wingman fallback. Current-user status and owner status do not prove the upstream account's session or operation permission.

`GET /apps/:id/connector/user-authorization` reports the authenticated editor's
own app grant, never another person's grant. It returns `status`,
`user_integrations`, `grant_integrations`, `authorization_url`,
`authorization_revision`, and `owner_grant`, without credentials.

`authorization_required` needs first approval; `reconnect_required` needs
approval again for changed or expired access. `connected` means the saved
grant matches the app, not that every provider account is healthy.
`not_required` needs no supported current-user grant; `unavailable` means
Connector OAuth is not configured. Existing legacy behavior is unchanged.

Craft Preview checks access before executing app code. Its Review access in
Connector action opens consent separately so editor buffers stay intact.
Returning to Craft rechecks access and resumes Preview automatically.
Integrations keeps Review access available for an already connected grant.
The returned start URL uses `force=true` so a current local grant does not
skip an explicitly requested new consent flow.

Account linking and app consent are separate. Do not borrow owner/server
credentials or copy a general Connector token to avoid this approval.
Ask the selected person promptly when consent is needed, and continue
independent work. Never approve on their behalf.

### Owner Connector Authorization

After saving the app's final integration settings and completing any requested publish, check whether the actual app owner needs to authorize app-owner integrations:

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/connector/owner-authorization" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

The token must belong to the app owner. Editors and platform admins receive `403`; no agent or admin can approve on the owner's behalf. The response does not expose any tokens and is not cached. Example when owner action is needed:

```json
{
  "status": "legacy",
  "cutover": false,
  "owner_integrations": ["google_sheets"],
  "grant_integrations": ["google_sheets", "jira"],
  "authorization_url": "https://wingman.shopee.io/hangar/api/auth/connector/start?app=APP_ID&include_owner=true"
}
```

`owner_integrations` use the owner's linked accounts on behalf of everyone who can use the app. `grant_integrations` is the full per-app grant for that owner; it can also contain current-user integrations, whose accounts are optional to link during consent. The owner must link the owner-mode accounts. Give the owner the returned URL to open in a browser; Hangar checks their identity, resumes through login if necessary, and redirects them to Connector's consent page. The agent must never visit or approve this link on the owner's behalf. After the owner says they approved, call this endpoint again once.

`not_required` means no supported owner-token integrations are configured. `legacy` means no prior owner grant exists: established standard providers may still use Wingman, but Order Admin and `gitlab`, `figma`, `notion`, `grafana`, `sea_transify`, `seller_portal`, and `smart` require Connector consent and cannot fall back. `connected` means the saved grant is active and matches app permissions, not that an upstream account or operation was tested. `reconnect_required` means owner cutover occurred but the grant is unusable; fallback remains disabled. `unavailable` means Connector is unconfigured or cannot prepare a grant; it does not make a new native provider usable through Wingman. Only `legacy` and `reconnect_required` supply an `authorization_url`; other statuses return `null`. Publication does not complete owner approval.

## Files

### List files

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/files" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

The file list returns path-level metadata by default, not file contents:

```json
{
  "files": [
    {"path":"backend/main.py","type":"file","size":1234,"sha256":"<64 hex characters>"}
  ],
  "revision": "<current app revision>",
  "source_hash": "<full app_source_hash of the current draft>"
}
```

`size` is UTF-8 **bytes**, not characters. `sha256` hashes those bytes.
Compare local byte hashes for diff/sync; the manifest avoids downloading all
source. `source_hash` pins the full draft for check/publication, including
unchanged-source releases. Ignore directory entries when comparing file hashes.
Use `?include_content=true` only when you intentionally need every file body.

### Staged Source Upload

Create or resume an upload with `POST /apps/:id/uploads`:

```json
{
  "revision": "<manifest revision>",
  "files": [{"path":"backend/main.py","size":1234,"sha256":"<64 hex characters>"}],
  "delete_paths": []
}
```

Send changed/new files only. Remote files not listed remain unchanged; missing
local source never implies deletion. Only explicit `delete_paths` removes
source. A deterministic identical manifest and base revision resumes staging.
This operation does not overwrite app metadata or table records.

Response:

```json
{
  "upload": {
    "id": "<upload ID>",
    "status": "uploading",
    "revision": "<base revision>",
    "missing": [{"path":"backend/main.py","offset":0,"size":1234}],
    "chunk_bytes": 262144
  }
}
```

`GET /apps/:id/uploads/:uploadId` returns the same `{upload}` envelope with
current offsets. Prefer `PUT /apps/:id/uploads/:uploadId` with a batch:

```json
{
  "chunks": [
    {"path":"backend/main.py","offset":0,"data_base64":"<base64 of raw UTF-8 bytes>"},
    {"path":"backend/helper.py","offset":0,"data_base64":"<base64 of raw UTF-8 bytes>"}
  ]
}
```

At most 128 chunks can share a request. Their **total** decoded raw bytes must
fit `chunk_bytes` (262144, 256 KiB); JSON must fit 512 KiB. Fill that shared
budget using each missing file's current byte offset. Small files share one
request; a large file can take the remaining budget and resume in the next
batch. Verify forward byte progress for every attempted chunk, not just the
first entry. The older singleton `{path,offset,data_base64}` remains supported.

Offsets and limits are bytes. A chunk may split a multibyte codepoint;
encode the full file once and slice bytes, not Unicode characters. Empty files
need no chunk. The server accepts an identical duplicate at the same offset.
If a batch response is lost or only a prefix of the batch was accepted, retry
the identical batch with the same upload ID, offsets, and bytes. Equal duplicate
chunks make partially accepted batches safe to resubmit. Do not start a new
session or guess offsets; retries must be bounded.

When `missing` is empty, send `POST /apps/:id/uploads/:uploadId/commit` with
`{}`. Hangar verifies every size/hash and commits all staged changes in one
revision-checked write:

```json
{
  "upload": {
    "id":"<upload ID>",
    "status":"committed",
    "revision":"<new revision>",
    "missing":[],
    "source_hash":"<committed full draft hash>",
    "app":{"id":"<app ID>","revision":"<new revision>"}
  },
  "app":{"id":"<app ID>","revision":"<new revision>"}
}
```

A revision conflict returns HTTP 409; stop and inspect concurrent edits rather
than forcing an overwrite. On commit timeout, query the session first. A
`committed` session supplies the completed hash; only an uncommitted session
may retry commit. Re-fetch the file manifest to verify source hashes and
preserved remote-only paths. Staging and commit save a draft, never publish it.
New apps and source-growing edits are limited to 80 MiB across the serialized
virtual filesystem. Existing apps already above the limit may stay level or
shrink, but may not grow. HTTP 413 means the app must remove embedded media or
large generated data and use separately uploaded app assets instead.
Old servers missing hash manifests or staged uploads must fail clearly; never
silently fall back to publishing whatever source happens to be saved.

### Read one file

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/files?path=frontend/src/App.svelte" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

### Upsert one file

```bash
jq -n --arg path "frontend/src/App.svelte" --rawfile content frontend/src/App.svelte \
  '{path:$path, language:"svelte", content:$content}' > /tmp/hangar-file.json

curl -sS -X PUT "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/files" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  -H "If-Match: $APP_REVISION" \
  -H "Content-Type: application/json" \
  -d @/tmp/hangar-file.json
```

File and asset mutation responses return compact app revision metadata by default. Add `?include=app` or `?view=full` only when you need the full updated app object echoed back.

### Delete one file

```bash
curl -sS -X DELETE "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/files" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  -H "If-Match: $APP_REVISION" \
  -H "Content-Type: application/json" \
  -d '{"path":"frontend/src/old-file.ts"}'
```

## Download / Upload App

The skill bundles `scripts/hangar_app.py` for local repository workflows. Use
`diff`, `pull`, `push --apply`, `metadata diff|pull|push`, `tables diff|pull|push`,
explicit record commands, `check`, and `release --apply` instead of ad hoc
upload loops. `tables push --apply` syncs definitions only, never records even
when local dumps contain them. `release` (also `deploy`) performs staged push,
definition-only table sync, pinned check, async publish wait, and fresh
authenticated shell/health verification. It never pushes `hangar-app.json` or
changes app identity/visibility/grants. Hosted Craft turns remain draft-only.
An ambiguous table-definition write is recovered with a schema-only read
before any bounded retry. An already-matching saved definition is accepted,
and a conflicting definition/revision stops instead of overwriting it.
Table definitions absent locally are preserved; no table/record deletion is
part of a release.

For a repository containing game/Node tools, use `--source-dir frontend/src
--source-dir backend --source-dir design` on diff/push/release. These scopes
preserve VFS paths and do not authorize remote deletions. Collection excludes
local credential/tooling directories such as `.local`, `.venv`, `dev`,
`.hangar`, `.env*`, and `.user-token`; see
[app development](app-development.md#sync-and-verify) for the full list.

### Download app zip

```bash
curl -L "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/export" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  -o "$APP_ID.zip"
```

The zip contains virtual filesystem files, `data/tables-manifest.json`, and `hangar-app.json` metadata. Table records are not included by default to avoid accidental huge exports. To include table dumps, pass `?include_tables=true`; each table is capped by `max_table_records` with a default of 1000 and a maximum of 100000:

```bash
curl -L "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/export?include_tables=true&max_table_records=2000" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  -o "$APP_ID.zip"
```

The metadata includes app identity, spaces, redacted settings, content fields, and design fields.

### Upload local app files

For a new app, `POST /apps` accepts a JSON array of files. For an existing app,
prefer staged source upload above, or a revision-checked `PUT /files` for a
single small edit. Legacy `PATCH /apps/:id` with `{"files":[...]}` replaces the
entire virtual filesystem; it is not a safe incremental sync and can exceed
request limits. The CLI does not fall back to this legacy replacement.

When uploading files that reference `$content` or CSS variables, also include or patch the matching top-level `content` and `design` arrays so Craft's Content and Design tabs remain usable. After patching, read `GET /apps/:id` and verify each `content.some_key` and each `var(--some-token)` in code has a corresponding app field.

For existing apps, treat Content and Design field values as source-of-truth app metadata. When a requested visual or copy change appears not to take effect after a file sync, inspect `GET /apps/:id` for an existing `content` or `design` field that is overriding the code fallback.

## Wingman Chat Workspace Files

These files live under `hangar_chat/<app-key>/<workspace>/uploads/`, not in Hangar's virtual app source files or asset storage. No actor or chat-session directory is added to the working folder. Only the app owner or a platform admin may manage them through the external API and Craft. Every chat from this app using the same workspace name can see its files. The app backend decides whether users share one name or use per-user names derived from authenticated identity; do not treat the name itself as an access-control check. The app's runtime may use HangarKit `wingman_chat.put_file()`, `list_files()`, `get_file()`, and `delete_file()` to access the same files.

```bash
export APP_ID="your-app-id"
export WORKSPACE="default"
export FILENAME="brief.md"
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/wingman-chat/workspaces" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/wingman-chat/workspaces/$WORKSPACE/files" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
curl -sS -X PUT "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/wingman-chat/workspaces/$WORKSPACE/files/$FILENAME" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" -H "Content-Type: text/markdown" \
  --data-binary @./brief.md
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/wingman-chat/workspaces/$WORKSPACE/files/$FILENAME" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" -o ./brief.md
curl -sS -X DELETE "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/wingman-chat/workspaces/$WORKSPACE/files/$FILENAME" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

Workspace names are 1-254 ASCII letters/digits/dots/dashes/underscores/`@`/`+` beginning with a letter or digit, so a typical email address can be a workspace name; filenames are flat names up to 128 characters using letters/digits/dots/dashes/underscores. No paths or subdirectories. The bot allows up to 10 MiB per file, 100 files and 50 MiB per workspace. `GET .../workspaces` returns `{"workspaces":["default",...]}` and listing files returns `{"files":[{"name":"brief.md","size":123,"path":"uploads/brief.md"}]}`. File download returns raw bytes.

## Assets

### List assets

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/assets" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

### Upload asset files

```bash
curl -sS -X POST "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/assets" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  -F "assets=@./logo.png"
```

### Delete an asset

```bash
curl -sS -X DELETE "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/assets" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename":"logo.png"}'
```

## Tables

### List tables

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/tables" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

### Update a table definition (preserves every record)

```bash
curl -sS -X PATCH "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/tables/tasks" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"schema":[{"name":"title","type":"text"}],"scope":"app"}'
```

The old full-table `PUT` replacement is **deprecated and disabled** (HTTP 410 with a `Deprecation` header). Do not send a record dump to `PATCH`: it rejects a `records` field. Use the row operations below or an explicit wipe. `DELETE /tables/:table` still removes the entire table definition and its rows; it is not a row wipe.

### Read a table

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/tables/tasks" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

Table reads are paginated by default and return up to 100 records unless `perPage` or `limit` is supplied. `perPage` has a legacy-compatible maximum of 500; prefer pages of 100 or fewer for new workflows, especially when records are large. Each record is limited to 10 MiB of JSON data.

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/tables/tasks?page=1&perPage=100&sort=-updated" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

Use `?schema_only=true` to read only schema/access metadata. Use `?dump=true` only when a full table dump is truly needed; full dumps are capped by `max_records` with a default of 1000 and a maximum of 100000, and by a 1 GiB JSON limit.

To download the same CSV export as Craft, use `?format=csv`. Hangar returns `<table>.csv`, or a ZIP containing that CSV when the CSV is at least 2 MiB. This exports up to 100000 records (subject to the 1 GiB JSON dump limit), independent of the JSON `max_records` default. Use `-OJ` so curl honors the returned filename:

```bash
curl -fsS -L -OJ "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/tables/tasks?format=csv" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

The bundled CLI offers `python scripts/hangar_app.py tables export --app "$APP_ID" --table tasks --output ./tasks`; it chooses `.csv` or `.zip` from the response. Neither export changes table data.

Send `If-Match: <table.updated>` or `"expected_updated": "<table.updated>"` for definition changes. This checks definition changes only, not runtime row writes.

### Record operations

Record `id` is the app-facing row key. It is unique within `(app, table, owner)`; for a user-scoped table pass `owner` on management requests. Use IDs, not list positions, for updates and deletes. List rows with `GET .../records?page=1&perPage=100` (and `&owner=<user-id>` for a user-scoped table), then:

```bash
curl -sS -X POST "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/tables/tasks/records" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" -H "Content-Type: application/json" \
  -d '{"id":"task-1","title":"Test"}'
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/tables/tasks/records/task-1" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
curl -sS -X PATCH "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/tables/tasks/records/task-1" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Updated"}'
curl -sS -X DELETE "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/tables/tasks/records/task-1" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

`POST .../record-batches` accepts `{"records":[...]}` and `DELETE .../record-batches` accepts `{"ids":["task-1","task-2"]}`. Each batch contains 1-100 rows/IDs; it is atomic, and any duplicate or missing delete ID rejects the whole batch. For user-scoped tables, add `"owner":"<user-id>"` to the batch body, to a single create/update body, or `?owner=<user-id>` to single GET/DELETE URLs. Runtime HangarKit instead derives user scope from the signed-in actor.

Storage-backed table-write failures return JSON with `error` and `request_id`. Record validation may return 400 with `code: "invalid_record"` and safe `fields`; duplicate row IDs return 409 with `code: "duplicate_record_id"`. An upstream rejection without field details returns a generic JSON 400, while unexpected storage failures return a generic JSON 500. Include `request_id` when reporting errors to Hangar support; internal PocketBase details are logged server-side.

To **wipe every row across all owners while retaining the table definition**, read `GET .../record-clear` for `record_count` and `revision`, then explicitly call:

```bash
curl -sS -X POST "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/tables/tasks/record-clear" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" -H "Content-Type: application/json" \
  -d '{"confirm":"tasks","expected_count":42,"expected_revision":"<revision from GET /record-clear>"}'
```

A count or data revision mismatch returns 409. This operation is destructive; export a backup first. It deletes in bounded batches, so a storage failure can leave a partial wipe; inspect the current state before retrying. `tables push` never invokes it.

## Publish and Backend

### Check frontend build

Compile the saved browser frontend without publishing (no server render):

```bash
curl -sS -X POST "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/check" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

Success response:

```json
{
  "success": true,
  "html_size": 12345,
  "body_size": 6789,
  "client_js_size": 4567,
  "hash": "abc123def456",
  "source_hash": "<full draft source hash checked>",
  "preview_url": "..."
}
```

Failure response includes `success: false`, `error`, and the app URLs. Fix check failures before claiming completion. A failed publish preserves the previous working code.
The returned `source_hash` describes exactly the draft checked, not merely a
frontend bundle hash. A release must compare it with the synced source hash.
After table-definition pushes, re-fetch the file manifest first and reject
any draft-hash mismatch; table schemas themselves are not in `app_source_hash`.
Unchanged-source check and publication reuse the server's compiled artifact.

### Publish app

Publish the saved draft only when requested. Wait for active editing turns to
finish. Check the response and verify the runtime URL; a saved or checked
draft is not a published release.

For reliable bounded publication, `POST /apps/:id/publish` accepts:

```json
{"async":true,"idempotency_key":"<fresh UUID>","expected_source_hash":"<verified draft hash>"}
```

HTTP 202 returns `{job, app_url, ...urls}`:

```json
{
  "job": {"id":"<job ID>","status":"queued","source_hash":"<verified draft hash>"},
  "app_url":"<published runtime URL>"
}
```

Poll `GET /apps/:id/publish/jobs/:jobId`. The response is `{job, ...urls}`.
Active statuses are `queued`, `building`, `starting_backend`, and `activating`.
Terminal statuses are `ready`, `failed`, and `superseded`; `job.result` and
`job.error` carry the outcome when available. Only `ready` with the matching
source hash is an activated result, and runtime verification is still needed.
An expected-source mismatch aborts instead of publishing concurrent edits.
Never report a queued/building request, failed job, or superseded job as live.

Generate a fresh UUID for each **new** publication. Keep it unchanged for
retries of an ambiguous POST: the same key returns the same job without
creating another version. After a lost POST response, retry only that key and
source hash; after a known job ID, resume GET polling. Jobs may resume unfinished
work after server process restart. Both requests and overall waits must be
finite. A wait timeout is not permission to create another publication.

`release --app "$APP_ID" --dir "$APP_DIR" --apply` retains non-secret recovery
state in `.hangar/release.json`. Re-run the same command to resume; do not
change the source/app/host or discard state while the old job is unresolved.
The default wait is 900 seconds, with `--wait-timeout` capped at 3600 and
`--poll-interval` between greater than zero and 30 seconds. `--json` prints
one final result to stdout; progress/status changes go to stderr.
`publish --app "$APP_ID" --job "$JOB_ID" --apply` polls an existing job only.
To recover a standalone ambiguous publish, reuse `--idempotency-key "$KEY"
--expected-source-hash "$SOURCE_HASH"` with `publish --apply`; do not invent a
new key. Failed/superseded jobs need inspection before deliberately removing
release state for a new attempt. Old servers fail without an automatic
synchronous publication fallback.

The older synchronous publish with an empty JSON body remains available:

```bash
curl -sS -X POST "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/publish" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

Success response includes `preview_url`, `published_version`, and, when a backend was started, `deployment`. `superseded: true` means no new code was activated. Post-commit schedule issues appear as `warning`; they do not undo the update. History and working code commit together for inline releases. Oversized releases skip history snapshots and atomically save an immutable release file instead; `snapshot_id` is omitted. The complete release, including compiled HTML, is limited to 512 MiB. Saved draft JSON field limits remain unchanged. Failure response includes `error` and `preview_url`.

New apps and source-growing edits support 80 MiB across the serialized virtual
filesystem, including frontend and backend files. Splitting source into smaller
files does not bypass this aggregate limit. Existing oversized apps continue to
run and may shrink, but cannot grow further.

Applying code never changes sharing. Use a partial `settings.visibility` patch only when the user requests Private, Unlisted, or Public. Do not prompt to enable discovery after an ordinary update.

If publish/backend deploy fails with `No module named uvicorn`, add `uvicorn` to `backend/requirements.txt`, sync it with `PUT /files`, and publish again.

### Backend status

External status describes the active release, not the separate Craft preview
process. External backend deploy restarts active code; it does not apply drafts.

```bash
curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/backend/status" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

### Deploy backend only

```bash
curl -sS -X POST "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/backend/deploy" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

Use backend deploy/status to check whether Python backend dependencies install and the runner starts. Frontend `POST /check` does not start the backend.

### Stop backend

```bash
curl -sS -X POST "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/backend/stop" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

## Runtime Verification

The external API bearer token authenticates `/api/external/hangar/*`. Published app runtime routes use Hangar browser/session auth, so a raw `curl "$preview_url"` may return 401 even when publish succeeded.

Runtime app access is signed-in by default. Private apps can be used by owners, editors, listed members, and platform admins; platform admins receive owner/editor-equivalent table grants.

Exchange the Wingman token for a Hangar browser/session cookie:

```bash
COOKIE_JAR="/tmp/hangar-session-cookies.txt"

curl -sS -c "$COOKIE_JAR" -X POST "$HANGAR_BASE_URL/api/auth/token/browser-session" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

Verify the app shell and a backend route with that cookie:

```bash
curl -sS -b "$COOKIE_JAR" "$PREVIEW_URL" -o /tmp/hangar-preview.html

curl -sS -b "$COOKIE_JAR" "$PREVIEW_URL/api/health"
```

The CLI release verifier uses a new in-memory cookie jar and token exchange
each time, sends no-cache shell/health requests, and never saves or prints
credentials/cookies. It refuses redirects and different-origin runtime URLs.
Its default health route is `/api/_hangarkit/health`, which checks runner
`status` and app ID. Override with `--health-path /api/health` when checking an
app's own JSON health route (`status: "ok"` or `ok: true`). Disposable local
`HANGARKIT_USER_TOKEN` uses the local header instead of a Wingman token exchange;
it is not production/browser auth. Shell/health checks prove reachability, not
UI interactions or integration correctness; exercise those separately.

For public backend endpoints, also verify the published route itself:

```bash
curl -sS "$PREVIEW_URL/api/task?task_id=missing"
```

If the route is a public multipart or form `POST`, use a standard HTTP client rather than a browser cross-site form post, and include matching `Origin` / `Referer` headers if runtime CSRF checks require them.

For an end-to-end file sync check, add a harmless marker to a local exported file, sync it, read it back, publish, and verify the published HTML contains the marker:

```bash
jq -n --arg path "frontend/src/App.svelte" --rawfile content frontend/src/App.svelte \
  '{path:$path, language:"svelte", content:$content}' > /tmp/hangar-file.json

curl -sS -X PUT "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/files" \
  -H "Authorization: Bearer $WINGMAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/hangar-file.json

curl -sS "$HANGAR_BASE_URL/api/external/hangar/apps/$APP_ID/files?path=frontend/src/App.svelte" \
  -H "Authorization: Bearer $WINGMAN_TOKEN"
```

## Backend Runtime Notes

`GET /backend/status` can briefly show `installing_requirements` while dependencies install. Wait a few seconds and re-check status before concluding the app backend failed.

## Troubleshooting

Common failure patterns:

- Callback verification fails or saved handler changes seem ignored:
  Confirm a published release exists and includes the handler—even if the app
  is Private. Save/check/Preview are not Publish. Preserve visibility and
  signature checks; ask the user to Publish after the Craft turn. For SeaTalk,
  a generic gateway HTTP 200 acknowledgement is not a verified challenge.
- Publish succeeds but runtime route still fails:
  Verify the published app URL with a browser-session cookie and test the real runtime route, not only the external API.
- Public backend route is still protected:
  Re-check `settings.public_endpoints` for exact method/path matching and confirm the route is under `/apps/:slug/api/*`.
- Secret-backed integration or provider call fails even though settings look correct:
  Confirm the secret shape uses `settings.services.secrets.variables[].key/value`, then make another backend request. Hangar automatically refreshes the backend with the saved secrets before forwarding that request; no manual restart or republish is needed. If it still fails, inspect backend status/logs and provider permissions without exposing secret values. Secrets affect both Preview and the published app, not just draft code.
- Long-running backend create route times out:
  Return the task id quickly, then run the heavy work after the response path is clear. Keep polling/health routes lightweight and responsive.
- Polling or health requests hang while a job is running:
  Move blocking or CPU-heavy work off the main FastAPI event loop or request path.
