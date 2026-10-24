---
name: hangar-app-developer
description: Create, edit, import, sync, and publish Hangar apps from a local coding workspace using the Hangar API.
metadata:
  short-description: Develop Hangar apps from a local workspace
  version: "2026.10.22.1"
---

# Hangar App Developer

Hangar is the source of truth; local files are working copies.
Work on the selected app; never replace an existing app with a new one.

## Setup

- Use the chosen public `HANGAR_BASE_URL`, defaulting to
  `https://wingman.shopee.io/hangar`. Agent operations use `/api/external/hangar`,
  never internal VM URLs or browser APIs. Report actual HTTP status/messages.
- Check `/api/skills/hangar-app-developer/version` against `skill-version.json`.
  Download a newer package or one whose same-version hash changed. Never downgrade.
- Use `WINGMAN_TOKEN` or `HANGARKIT_WINGMAN_TOKEN` when set. Otherwise the bundled
  CLI reads a valid `~/.wingman/auth.json`. If no credential is available, ask
  for Wingman Desktop sign-in or a token from Wingman's connectors/token page.
  Never print credentials or put them in app files.
- Scope app-code searches to the app's working directory. For broad searches
  of this skill, exclude bundled templates: `rg -n -g '!templates/**' 'pattern' .`
  from the skill root. When a template is relevant, use `templates/INDEX.md`
  to choose one, then search only that template's folder.

## Workflow

1. Inspect the app via CLI or [API](references/external-api.md). Start new apps
   from a [template](templates/INDEX.md) or local source. Preserve chosen names
   and slugs; replace generated starter names in `name` and
   `settings.project_title`, not just page copy.
2. Read [app development](references/app-development.md) and the current
   `design/design.md`. Pull into the chosen app folder; inspect `diff` first if
   local files already exist. Do not force-overwrite unsynced work.
3. Implement the request. Read the relevant [capability](references/hangarkit.md)
   before using a helper; never invent signatures or load every provider.
4. Review the hash-based diff, sync coherent changes, and run `check`.
   Source sync saves a revision-checked draft, not a release.
   Keep metadata and records separate.
5. Publish only when requested; verify in a fresh authenticated session before
   claiming it works. Otherwise report
   the draft and checks. For callbacks, remind the user to Publish first—even
   Private apps need a release. Draft handler edits need republishing.

## Shared-server safety

- Read [limits and efficiency](references/hangarkit/workflow/app-performance.md)
  before data, integration, polling or background changes; Node/storage is shared.
- For "make it faster", consider pagination, batching, caching and progressive
  disclosure/fetching when useful. Preserve functionality, freshness and
  permissions; explain tradeoffs.
- Reuse work; bound total work, not just memory/concurrency.
- Start with 20–50 rows/page and 1–2 concurrent requests/view or job.
  No eager fetch-all, per-row fan-out or overlapping polls.
- Treat resource limits as ceilings; back off on 429/503 and verify writes before retrying.
- Caller-only SDK testing: [Kit API](references/hangarkit/runtime/kit-api.md).
- Prefer [Drive](references/hangarkit/backend/integrations-google-drive.md) for user-managed files.
  Use user auth for new per-user ownership. Store IDs/metadata, not bytes;
  keep static app assets in Hangar.
- Save changed fields. Bound caches/retries. Scratch is disposable; preserve
  durable work, unsynced edits and recovery state.
- Verify interactions and payloads, not just `check`; report unmeasured work.

## CLI

Use real app references and folders.

```bash
python scripts/hangar_app.py diff --app "$APP_ID" --dir "$APP_DIR"
python scripts/hangar_app.py push --app "$APP_ID" --dir "$APP_DIR" --apply
python scripts/hangar_app.py check --app "$APP_ID"
python scripts/hangar_app.py release --app "$APP_ID" --dir "$APP_DIR" --apply
```

`push` previews without `--apply`. Only explicit `--delete` removes remote-only source.
Uploads resume with the same manifest/base revision in bounded chunks; never
fall back to a full-app PATCH. See [sync details](references/app-development.md#sync-and-verify).
To exclude local tooling, add `--source-dir frontend/src
--source-dir backend --source-dir design` to `diff`, `push`, or `release`.
Never upload credentials; `.env*`, `.local`, `.venv`, `dev`, and CLI state are
excluded. Scoping does not imply remote deletion.
`metadata diff|pull|push` handles `hangar-app.json`; `tables push` changes only
definitions. Requested `release --apply` (`deploy --apply`) syncs, checks,
publishes, and verifies shell/runner, not interactions. It leaves metadata and
visibility unchanged. Resume with the same command; never discard unfinished
jobs to bypass timeouts. See [recovery](references/app-development.md#sync-and-verify).
Use `--help` for options.

## References

- Importing a repository: [import checklist](references/import-existing-project.md).
- App helpers and integrations: [HangarKit index](references/hangarkit.md),
  then the named capability page. For browser-backed integrations, read
  [Relay](references/hangarkit/connector-integration/relay.md) first.
- Native Connector APIs: read the [shared contract](references/hangarkit/connector-integration/native-apis.md)
  and provider page for error handling; no Relay setup. Google Sites also needs
  its [async job workflow](references/hangarkit/connector-integration/google-sites.md).
- Sharing changes: [sharing and publishing](references/hangarkit/runtime/sharing.md).
- Local backend tests: [Python SDK](references/hangarkit/backend/local-python-sdk.md).
- POP: [feature requests](references/pop-feature-requests.md).

Preserve visibility and grants unless asked to change them. Code rollback
does not undo records, secrets, assets, or external actions. Destructive record
operations and app deletion require the user's explicit intent.
