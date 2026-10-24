# App sharing and publishing

ID: `runtime.sharing`
Category: `runtime`

Private, Unlisted, and Public control audience; saved code remains a draft until explicit publishing.

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `settings.visibility`
- `settings.delivery`

## Details

## Sharing

`settings.visibility` is authoritative. All three choices require Hangar sign-in.

| Value | Runtime access | Catalog discovery |
| --- | --- | --- |
| `private` | Owner, editors, invited members, allowed teams, and platform admins | Only eligible people |
| `unlisted` | Any signed-in user with the URL | Only owner, explicit email/team grantees, and platform admins |
| `public` | Any signed-in user | All signed-in users |

New apps are Private without an implicit owner-department grant. An Unlisted
link can be forwarded; it does not grant catalog discovery or editing rights.
Unpublished apps are management-only, visible to owners, editors, and admins.
Catalog cards use Private, Unlisted, and Public labels rather than
Draft/Disabled. Publication status is separate.

Change sharing with a partial patch such as
`{"settings":{"visibility":"unlisted"}}`. Do not change visibility as a side
effect of editing or publishing. Use `visibility` instead of the legacy
`catalog_enabled` and `permissions.access` fields. Existing grants and links
remain compatible; opening an app never publishes its draft.

The Publish dialog manages Email and Team grants. Changing audience or grants
does not publish code. Private restricts subsequent requests immediately, but
cannot recall already downloaded content.

## Team Grants

`settings.permissions.departments` contains arrays of full Wingman hierarchy
paths, for example `[["Company", "Engineering"]]`. Grants default to Can use.
Use full path names: use-access matching is case-insensitive and prefix-based
per segment, so `Engineering` can also match `Engineering Operations` and
descendants. A root path covers that organization.

Explicit Can edit also requires the allowed path in
`settings.permissions.editor_departments`, a subset of `departments`.
Editing matches whole hierarchy segments and includes subteams, not
similarly named teams. Team editors have the same editing and sharing powers
as email editors, but not ownership or deletion authority.
Removing an allowed team also removes its edit grant; do not promote use
grants into editing implicitly. Grants are additive, so removing one does
not revoke access supplied by another grant.

Membership uses the authenticated Wingman department profile, not an email
domain. Team grants restrict the audience only when visibility is Private;
Public and Unlisted retain their broader signed-in runtime audiences.

## Publishing

Source, Content, and Design edits save a draft. Preview uses the draft, while
the app's runtime URL continues serving its published version. Publish
explicitly to release saved changes, after active agent turns finish.
Private apps can be published and run too; publishing never changes audience.

Callbacks also execute the published release, even for Private apps. Publish
before provider verification and republish changed callback code. A public
callback route bypasses browser sign-in, not publication or signature checks;
neither Preview nor changing visibility activates a draft handler.

Publishing reuses cached browser bundles for unchanged frontend source. Content,
Design, routes, and app-scoped helpers are generated for the current release.
App content appears after JavaScript loads. Frontend-only publishes can reuse
the running backend when its source, dependencies, credentials, and runtime
configuration match; preview and live backend processes remain separate.

External developers use `POST /api/external/hangar/apps/:id/publish`.
For bounded release work, send `{"async":true,"idempotency_key":"<fresh UUID>",
"expected_source_hash":"<verified draft source_hash>"}`. HTTP 202 means queued,
not published. Poll `GET /api/external/hangar/apps/:id/publish/jobs/:jobId`
through `queued`, `building`, `starting_backend`, and `activating` until
`ready`, `failed`, or `superseded`. Reusing the same key returns the same job
without another version; keep the original key on ambiguous POST outcomes.
Jobs can resume unfinished work after process restart. Do not start a new job
because the client stopped waiting. The synchronous empty-body publish API
remains available for existing clients.

The developer CLI's `release --app "$APP_ID" --dir "$APP_DIR" --apply` stages
source in bounded multi-file byte batches, syncs table definitions only, checks the same
draft hash, waits for async publication, and verifies a fresh authenticated
shell and runner health. It does not upload app metadata, change sharing,
or operate on records. Remote-only source is preserved unless `--delete`
was explicit. Re-run the same command after interruption to resume its saved
key/job; `.hangar/release.json` contains no credentials. The default wait is
900 seconds (`--wait-timeout`, maximum 3600). A changed source hash stops the
release instead of publishing concurrent edits. Checks and publication reuse
the compiled artifact when the source is unchanged.

Check the returned status and runtime URL. `superseded: true` means the
requested release was not activated. Do not equate a saved edit, successful
frontend check, or queued request with a verified working release.
`settings.delivery` provides status, errors, and warnings; it is read-only
operational metadata, not an audience setting.

Failed builds or backend starts preserve the previous published code.
Backend status/deploy endpoints target the active version; restarting a
backend is not a way to publish draft source. Open a fresh runtime page to
verify a release because existing browser tabs can retain an older bundle.

Releases above the inline snapshot budget are stored as an immutable release
file and do not create a history snapshot. The release still freezes published
code separately from drafts and is committed atomically with its version
pointer. The complete release, including compiled HTML, must fit within
512 MiB. This changes release storage, not the existing JSON limits on saved
draft fields. On the first oversized publish, Hangar raises the existing
published-file field limit as needed; no database migration is required.
Raw release files contain backend source and require editor
access; app users continue receiving only the rendered HTML.

## Shared Effects

Preview has separate code and test records. Table definitions, assets,
credentials, permissions, and external effects are shared. Code rollback
does not restore data or undo external operations. Avoid destructive work
at backend import/startup, which can also execute during checks or preview.

Secret changes apply on the next backend request without publishing source.
They affect both preview and the published app. Provider outages, expired
credentials, and failed schedule reconciliation must be reported as such.

Exact callback routes in `settings.public_endpoints` deliberately bypass
sign-in. Making an app Private does not disable these callbacks; app code
must validate provider signatures or secrets.
## Related capabilities

- `runtime.routing`
- `backend.cron`
