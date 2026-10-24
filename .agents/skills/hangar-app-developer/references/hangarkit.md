# HangarKit Runtime Reference

This is the generated index for the HangarKit reference. Read this index to choose the smallest relevant capability page, then read that page before writing or reviewing code that calls a HangarKit helper.

HangarKit modules are injected by Hangar at app build/runtime:

- Frontend virtual modules such as `$hangarkit`, `$data`, `$content`, and `$design` are provided by Hangar's compiler/runtime.
- Python backend module `hangarkit` is provided by Hangar's live backend runner and by the local Python SDK for user-local backend testing.
- Frontend virtual modules are not expected to resolve in a plain user-local app folder unless that folder is being built or run by Hangar.

## How to use a capability page

1. Select the page for the module or workflow you need.
2. Read its **Function inputs** section before calling a function. It lists the supported parameters and defaults.
3. Read its **Details** section for accepted object fields, limits, side effects, response shapes, and examples. Do not guess undocumented parameters.

## frontend

- [$hangarkit frontend helpers](hangarkit/frontend/hangarkit.md) — App-scoped helpers for backend calls, assets, external proxying, auth, low-level storage, cache, preferences, and prefix-safe navigation.

## data

- [$data persistent realtime collections](hangarkit/frontend/data.md) — Reactive app-scoped database access for generated frontend apps.

## content

- [$content editable content fields](hangarkit/frontend/content.md) — CMS-like app content values editable from the Content panel without code changes.

## design

- [Design fields and CSS variables](hangarkit/frontend/design.md) — Themeable design values exposed as CSS variables and editable from the Design panel.

## backend

- [Python backend hangarkit module](hangarkit/backend/hangarkit.md) — Request-aware Python helpers for app context, URLs, assets, cache, short links, and app-scoped table access.
- [Scheduled cron jobs](hangarkit/backend/cron.md) — Register published Python functions for Hangar-managed scheduling, wake-up, retries, run history, and manual execution.
- [Document conversion](hangarkit/backend/documents.md) — Convert supported office documents to PDF through Hangar's private, LibreOffice-backed worker.
- [Local Python HangarKit SDK](hangarkit/backend/local-python-sdk.md) — Local development package for running backend/main.py with live-compatible Python hangarkit imports and app-scoped mock routes.
- [Python backend cache](hangarkit/backend/cache.md) — App-scoped ephemeral cache helpers for backend code.
- [Email](hangarkit/backend/email.md) — Send email from backend code through Hangar's audited, quota-limited email gateway.
- [Platform short links](hangarkit/backend/short-url.md) — Generate platform short links from app backend code and let Hangar maintain the review record.
- [Python backend integrations](hangarkit/backend/integrations.md) — Backend integration packages under hangarkit.integrations for connector-backed services, Relay portals, SeaTalk, Wingman Chat, and LLM Chat.
- [ABTest integration](hangarkit/backend/integrations-abtest.md) — Call AB Test Platform MCP tools through Wingman ABTest proxy from backend code.
- [Confluence integration](hangarkit/backend/integrations-confluence.md) — Read and write Confluence pages, content, attachments, and comments from backend code.
- [Google integration](hangarkit/backend/integrations-google.md) — Call Google APIs through Hangar integration auth when a provider-specific helper does not exist yet.
- [Google Docs integration](hangarkit/backend/integrations-google-docs.md) — Create, read, update, and extract text/markdown from Google Docs through Hangar integration auth.
- [Google Drive integration](hangarkit/backend/integrations-google-drive.md) — List, search, upload, replace content, manage metadata and folders, export, and share Google Drive files.
- [Google Mail integration](hangarkit/backend/integrations-google-mail.md) — Search, inspect, draft, send, label, archive, trash, and read Gmail attachments from backend code.
- [Google Sheets integration](hangarkit/backend/integrations-google-sheets.md) — Create spreadsheets and read/write Google Sheets values and sheets from backend code.
- [Jira integration](hangarkit/backend/integrations-jira.md) — Search, read, create, update, transition, comment on, and attach files to Jira issues.
- [Log Platform integration](hangarkit/backend/integrations-log-platform.md) — Search live and nonlive Log Platform logs from backend code by CMDB/query, trace id, or copied Log Platform URL.
- [LLM Chat integration](hangarkit/backend/integrations-llm-chat.md) — Make raw OpenAI-compatible Chat Completions calls through Hangar, with caller-configured tools and request options.
- [SeaTalk integration](hangarkit/backend/integrations-seatalk.md) — Build SeaTalk bots, verify callbacks, send messages, inspect chats, and use SeaTalk contacts/group APIs.
- [SPACE integration](hangarkit/backend/integrations-space.md) — Call SPACE APIs through the default SPACE proxy or a specific SPACE domain proxy.
- [Platform integrations](hangarkit/backend/integrations-platform.md) — Platform and proxy-backed backend helpers for POP, PMP, and Wingman Chat.
- [Platform SeaTalk groups](hangarkit/backend/platform-seatalk.md) — Create and manage SeaTalk groups through platform-owned bots, without SeaTalk bot credentials or app integration configuration.
- [Platform Toolverse helpers](hangarkit/backend/platform-toolverse.md) — Look up API ownership, identifiers, and encoded extinfo with no app credentials or generic Toolverse client.
- [PMP integration](hangarkit/backend/integrations-pmp.md) — Call PMP APIs from backend code with the configured user or app-level integration auth.
- [POP integration](hangarkit/backend/integrations-pop.md) — Call Product Operation Platform tools through Wingman POP proxy from backend code.
- [Wingman Chat integration](hangarkit/backend/integrations-wingman-chat.md) — Submit a managed Wingman Chat turn and poll its bot-owned run without holding an HTTP request open.

## connector_integration

- [Connector and Browser Relay](hangarkit/connector-integration/relay.md) — Explain browser-backed integrations to first-time app builders and users, and design their setup and recovery flow.
- [Relay portal integrations](hangarkit/connector-integration/relay-portals.md) — Discover and call cataloged Relay portal operations with provider-scoped access and recovery.
- [Order Admin](hangarkit/connector-integration/order-admin.md) — Build Order Admin workflows with cataloged operations, Connector grants, and target-scoped Relay recovery.
- [Promotion Admin](hangarkit/connector-integration/promotion-admin.md) — Build regional Promotion Admin features with current-user consent and a verified portal API contract.
- [CMT Admin](hangarkit/connector-integration/cmt-admin.md) — Use CMT Admin's own regional target set and current-user Relay session in a Hangar app.
- [Product Label Admin](hangarkit/connector-integration/product-label-admin.md) — Use the environment-scoped Product Label Admin portal without inventing a region selector.
- [SSC Ops](hangarkit/connector-integration/ssc-ops.md) — Route SSC Ops by environment and supply operation-specific project and country headers separately.
- [User Admin](hangarkit/connector-integration/user-admin.md) — Use User Admin's required market context on its shared environment host with current-user consent.
- [Listing Admin](hangarkit/connector-integration/listing-admin.md) — Build Listing Admin workflows on an explicitly chosen environment and current-user website session.
- [BD Centre](hangarkit/connector-integration/bd-centre.md) — Build BD Centre operations with environment routing and Connector-managed session/CSRF handling.
- [TWS](hangarkit/connector-integration/tws.md) — Use the Global TWS environments supported by HangarKit and distinguish Connector's separate CN/live route.
- [DataSuite](hangarkit/connector-integration/datasuite.md) — Use DataSuite's fixed host and current-user browser session without inventing target options or catalog operations.
- [SeaTalk Open Platform](hangarkit/connector-integration/seatalk-open.md) — Use the browser-backed SeaTalk Open developer portal, distinct from messaging and app-credential APIs.
- [Skyline](hangarkit/connector-integration/skyline.md) — Build against Skyline's fixed digital-QA test host and verify APIs independently of a successful portal sign-in.
- [Traffic Suite](hangarkit/connector-integration/traffic-suite.md) — Use Traffic Suite's fixed live portal with current-user grant, IDaaS sign-in, and operation-specific validation.
- [CS Portal](hangarkit/connector-integration/cs-portal.md) — Use regional in-house CS Portal APIs with the current user's grant and website session.
- [DMS CS Portal](hangarkit/connector-integration/dms-cs-portal.md) — Use the separately authenticated DMS CS Portal and its regional API contracts.
- [Seller SOP](hangarkit/connector-integration/seller-sop.md) — Use regional Seller SOP browser access, distinct from native Seller Portal Open APIs.
- [ShopeeFood Admin](hangarkit/connector-integration/shopeefood-admin.md) — Use ShopeeFood Admin's own environment/market set and Connector-managed CSRF handling.
- [Noti Admin](hangarkit/connector-integration/noti-admin.md) — Use environment-scoped notification administration APIs without inventing a regional target.
- [Chat Admin](hangarkit/connector-integration/chat-admin.md) — Expose Chat Admin's environment-scoped Connector APIs while reporting the current Relay CLI support limitation honestly.
- [Listing QC Admin](hangarkit/connector-integration/listing-qc-admin.md) — Use the separate Listing QC portal with environment routing and Connector-managed sessionId.
- [SOUP](hangarkit/connector-integration/soup.md) — Use environment-scoped SOUP portal APIs without treating them as a cookie-export or universal login API.
- [Leave Portal](hangarkit/connector-integration/leave-portal.md) — Use the fixed Sea leave portal with current-user browser access and privacy-aware workflow handling.
- [MP AI DOD](hangarkit/connector-integration/mp-ai-dod.md) — Call the fixed staging AI DOD portal with current-user access and reviewed operation contracts.
- [Google Sites](hangarkit/connector-integration/google-sites.md) — Start and poll browser-executed Google Sites page and asset reads without exporting Google cookies.
- [Native Connector APIs](hangarkit/connector-integration/native-apis.md) — Build native linked-account integrations without confusing app consent, provider credentials, or browser Relay.
- [GitLab](hangarkit/connector-integration/gitlab.md) — Use GitLab APIs with an app-scoped Connector grant and optional configured GitLab target selection.
- [Figma](hangarkit/connector-integration/figma.md) — Call reviewed Figma APIs with Connector-managed OAuth access rather than browser Relay or pasted credentials.
- [Notion](hangarkit/connector-integration/notion.md) — Use versioned Notion API contracts while Connector manages linked OAuth or token authentication.
- [Grafana](hangarkit/connector-integration/grafana.md) — Use the selected linked Grafana domain and organization without exposing session or service-token material.
- [Sea Transify](hangarkit/connector-integration/sea-transify.md) — Call project-authorized Sea Transify APIs with a Connector-managed translation credential.
- [Seller Portal](hangarkit/connector-integration/seller-portal.md) — Use native Seller Portal Open APIs without confusing them with the browser-backed Seller SOP portal.
- [SMART](hangarkit/connector-integration/smart.md) — Use Connector's SPACE-derived SMART credential for native APIs and MCP tools, separately from template schema import.

## workflow

- [Efficient app implementation and verification](hangarkit/workflow/app-performance.md) — Protect shared Hangar capacity with small pages, bounded payloads/concurrency, safe retries, and measured runtime behavior.
- [SMART workflow runner template](hangarkit/workflow/smart-workflow-runner.md) — Create a task runner for one deployed SMART workflow, using either a pasted input schema or administrator-managed SMART Project schema import.

## runtime

- [Single-domain app routing](hangarkit/runtime/routing.md) — Public apps are served by path, not custom domain: {host}{HANGAR_APP_PREFIX}/apps/:slug.
- [Caller-only HangarKit API](hangarkit/runtime/kit-api.md) — Discover public Python HangarKit methods and invoke supported methods through one caller-permission gateway, without deploying an app backend.
- [App sharing and publishing](hangarkit/runtime/sharing.md) — Private, Unlisted, and Public control audience; saved code remains a draft until explicit publishing.
