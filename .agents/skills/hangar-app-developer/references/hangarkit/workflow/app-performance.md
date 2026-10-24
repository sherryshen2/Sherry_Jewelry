# Efficient app implementation and verification

ID: `workflow.app_performance`
Category: `workflow`

Protect shared Hangar capacity with small pages, bounded payloads/concurrency, safe retries, and measured runtime behavior.

## Caller guidance

This page documents a workflow rather than a callable helper. Follow its ordered steps and use the linked capability page before calling a runtime API.

## Details

Make the primary workflow useful quickly and keep typing, scrolling, and
navigation responsive with representative data. Choose the simplest approach
that meets the requested experience; visual polish does not justify loading
every record, full-resolution image, or background feature at startup.

## Choose sensible defaults for nontechnical users

Most Hangar users have no programming background. They may ask for a dashboard
or say "make the app faster" without knowing which techniques exist. Consider
the following during relevant builds and performance fixes; choose the smallest
useful combination, not all five by default. Keep small, fast apps simple.

| Technique | When it helps | Preserve correctness |
| --- | --- | --- |
| Pagination | Growing lists: fetch the visible page, with Next or Load more. | Preserve global search, sorting, totals and exports where required; label page-local results. Use stable identities and deduplicate overlapping pages without merging distinct records. |
| Batching | Many similar calls: use documented bulk endpoints in bounded chunks. | Respect row/byte limits and per-item failures. Parallel individual calls are not batching; never blindly replay a partially successful write batch. |
| Caching | Repeated or slow-changing reads: reuse bounded, authorized results and share identical in-flight reads. | Scope keys by user/access context and inputs; set freshness/invalidation rules, distinguish stale data, and keep action authorization/preflights fresh. |
| Progressive disclosure | Secondary details, advanced filters or expensive charts: reveal them when needed. | Keep essential information and actions discoverable and accessible. Hiding a panel alone does not reduce fetching; defer its data/work too when appropriate. |
| Progressive fetching | Independent sections or details: show useful results as they arrive, then fetch more on demand or in bounded stages. | Don't block the whole screen on the slowest section or eagerly fetch every hidden page. Keep loading, partial, stale, empty and failed states distinct; discard obsolete responses after navigation/filter changes. |

Preserve the user's workflow, complete-result requirements, permissions and
external actions. Do not make an app "faster" by silently dropping records,
weakening freshness guarantees or disabling background duties. If changing a
shared request limit/cache affects several screens, inspect each affected
consumer rather than optimizing only the first one. Partial data must not be
presented as a complete total or used for actions requiring complete evidence.

Make routine engineering choices within the requested task. Ask about product
tradeoffs only when they materially change the experience, such as how old
displayed data may be. Explain outcomes in plain language: "Show the first
results quickly and load details when opened," not "Do you want pagination?"
Verify the visible workflow with representative data, including first load,
subsequent pages/details, refresh and failure recovery; a successful API response
does not prove the browser rendered it. Report measured gains and remaining waits.

## Shared capacity and safety ceilings

App table calls and storage JSON decoding use Hangar's shared Node/storage
services even when initiated by a Python backend. Low Python CPU or a
per-backend resource limit does not isolate this work. The VM's RAM and Node
heap are not an app's memory allocation. Design for many viewers and jobs
sharing the server, not just one successful test request.

Current platform limits/defaults are below. Operators can override configurable
limits; the deployed server is authoritative. Do not raise limits or move work
to another route to evade them while building an app.

| Boundary | Current limit/default | App design consequence |
| --- | --- | --- |
| Public app API responses through Hangar ALB | 20 MiB per response for app API, data, cache, and integration routes | Return compact data and file references. Streaming does not bypass the byte limit; use authorized Drive viewing/downloading when appropriate. |
| Drive single-request upload helpers | 20 MiB raw file content; 64 KiB JSON metadata | A buffered upload safety ceiling, not a Google file-size limit. Larger files need a separate resumable workflow; do not split content into ordinary create/update calls. |
| Runtime/preview data operations | 8 active per app, 64 per Node process | Shared across viewers and jobs, not eight per browser. Excess returns 429; there is no waiting queue. |
| Storage SDK requests | 16 per identified app, 64 per process; 120-second deadline | Includes waiting for headers and JSON consumption. Not an end-to-end app job timeout or a latency target. |
| Storage JSON decoding | 128 MiB per response, 256 MiB across active decodes; 8 per identified app, 16 per process | Limits count received bytes, not total heap. Parsed objects and retained results can use more memory. |
| Table reads | 100 rows by default; maximum `perPage` 500 | Set a smaller explicit page size; row count alone does not bound bytes. |
| Record writes | 10 MiB JSON per record | Keep large payloads/media out of records; fetch compact summaries for lists. |
| Batch record writes | 1–100 records/IDs; 16 MiB JSON batch budget | Batch by bytes as well as count; maximum-sized records cannot all fit in one batch. |
| App source | 80 MiB serialized virtual filesystem for new/growing source | Source is code, not a dataset or binary file store; legacy exceptions are described below. |
| Persistent table data | Default 5 GiB logical JSON per app | Storage quota is not permission to load that data into memory; see the data reference for quota accounting. |

All are safety ceilings, not performance targets. For ordinary interactive
lists, start with 20–50 compact rows, aim for roughly 1 MiB or less of JSON per
response, and use 1–2 concurrent requests per view/job. These are design
starting points, not enforced limits or reserved capacity. Leave headroom for
other viewers, previews, and jobs; reduce work when busy.

## Minimize disk use; temporary files are disposable

- Prefer streaming or bounded in-memory processing in both agent workflows
  and generated app backends. Avoid full dataset downloads, repeated archive
  extraction, local backup copies, and disk caches when unnecessary. Do not
  replace disk growth with unbounded memory use; process large inputs in chunks.
- Runner workspaces, `/tmp`, and app-created local caches may be cleared at
  any time. Never rely on them as the only copy of app state or a durable file
  reference. Save source drafts through Hangar's file API, structured app data
  through records, and durable files through Drive or Hangar assets as
  appropriate. This does not make
  Hangar-managed assets or published releases disposable.
- If a library requires a filesystem path, use a task-owned temporary directory
  with bounded input/output sizes and concurrency. Clean up in a context manager
  or `finally`, including on errors. Missing scratch files must produce a safe
  retry/rebuild from durable inputs, not lost data or an infinite retry loop.
- Do not accumulate per-request clones, virtual environments, backups, or
  downloads. Reuse necessary tooling while available. Clean only scratch files
  owned by the task; preserve shared files, unsynced source, and unfinished
  upload/release recovery state. An empty workspace is not an empty Hangar app.

## Files stay out of source and records

New apps and source-growing edits are limited to 80 MiB across the serialized
virtual filesystem. The limit is aggregate, not per file. Existing legacy apps
already above the limit may be edited to stay level or shrink, but cannot grow
further; very large reads are also subject to the storage-response safeguards
below. When a save returns HTTP 413, remove embedded
media or generated data and store it in Drive or as an app asset, as appropriate.

- Prefer Google Drive for user-managed uploads, documents, and generated files
  when appropriate. Use current-user auth for new workflows where users should
  own their files; preserve explicitly selected shared-account access. Read the
  Drive capability before using its helpers, and never widen file sharing or
  migrate existing assets automatically.
- Keep application-owned static media and existing app assets in Hangar. Store
  only Drive file IDs/links or asset filenames/references and compact
  metadata in records, Content, settings, and source. Do not turn files into
  base64/data URLs, numeric byte arrays, giant SVG path literals, or JSON blobs
  to bypass source-upload limitations. Small hand-authored icons/SVGs are fine.
- When using Hangar-managed assets for browser uploads, define a `file` or
  `files` field and pass the browser
  `File` directly to `$data.create()` or `$data.update()`. Display the stored
  filename with `asset(filename)`. Developer workspaces upload binary files
  through the external API's multipart assets endpoint, separately from text
  source sync; read the external API reference in the developer skill.
- Reuse attachments that are already app assets by their stored filename.
  Do not transcribe or regenerate their bytes into code. If the current toolset
  cannot upload a required asset, explain that limitation and use an existing
  asset or a lightweight placeholder; do not embed the binary as a workaround.
- For temporary browser previews, use an object URL and revoke it when replaced
  or disposed; never save a `blob:` URL as a durable reference. If a provider
  explicitly requires base64 (for example SMART input), encode only at that
  request boundary, bound the input, and omit the encoded bytes from saved
  records, logs, and response history. Transport encoding is not a storage format.
- Resize/compress images to their display needs before upload when tooling is
  available. Use thumbnails for grids and originals for explicit detail/download
  actions. Hangar currently generates only the cropped `640x360` preset; other
  sizes return originals. Use uploaded derivatives for other sizes/aspect ratios.
  Verify the actual returned image dimensions
  and bytes; a thumbnail query parameter alone is not proof of optimization.
  Reserve image dimensions or aspect ratio, lazy-load offscreen images, and
  avoid lazy-loading the primary above-the-fold image. Use posters and
  `preload="none"` or `"metadata"` for media that the user has not played.
- Preserve existing records and references during a targeted fix. Do not bulk
  rewrite legacy inline media, delete originals, or change sharing without
  authorization for that work.

## Bound data, requests, and persistence

- For growing collections, load the visible page with `page({ page, perPage,
  filter, sort })`; typically start with 20–50 rows and expose pagination or
  Load more. `list()` and `subscribe()` are also paginated: their first result
  is not the entire dataset. Do not loop through every page during initial
  rendering or label a first-page total/filter as a global result. Replacing
  one giant request with eager fetching of every page still overloads the
  server. Virtualizing the UI does not reduce fetched or parsed data.
- Use only documented filter/sort options. If global search or aggregation
  needs more than the supported query can express, design an appropriate
  backend workflow or maintained summary; do not silently fetch all records
  into the browser. Keep large detail/debug payloads separate from list data
  and fetch them only when opened. Do not assume an undocumented projection,
  aggregation, or index API exists.
- Fetch only what the current view needs. Batch supported operations, avoid
  per-row request waterfalls, and use bounded concurrency for independent
  calls (start with 1–2 at a time), not unbounded `Promise.all` or
  `asyncio.gather` over records. Do not create a new concurrency pool for each
  row or page. A four-request pool in every browser can still overload the app.
  Debounce remote search, ignore stale responses, and avoid duplicate requests
  from overlapping effects, subscriptions, and polling.
- Keep related large payloads out of list records: return compact status,
  counts, IDs, and asset references, then load details on demand. Do not
  duplicate full provider responses, HTML, logs, or history on every record.
  Splitting one payload across records only helps if those records are not
  all fetched and concatenated again. Never discard user data as an optimization.
- Save changed fields rather than reserializing the full dataset on each
  keystroke or pointer move. Debounce/coalesce frequent edits or save on commit,
  flush pending changes appropriately, and retain unsaved input on failure.
  Keep history bounded and change-based when large documents are editable.
- Use finite timeouts, bounded retries with backoff, and no overlapping poll
  requests. Schedule the next poll after the previous finishes; stop at terminal
  states and pause unnecessary refresh while hidden. Coalesce realtime bursts;
  do not combine a subscription with a second full-list polling loop.
  Release timers, subscriptions, and listeners on disposal.

### Bulk work is explicit, incremental, and resumable

Full scans belong only to an explicitly needed export, import, sync, or
aggregation workflow, not page load, each search, each viewer, or each poll.
Do not simply move a browser fetch-all loop into a Python endpoint.

- Process one page/chunk, persist or emit the useful result, discard it, then
  fetch the next. Bound rows, bytes, elapsed time, and job concurrency; do not
  accumulate all pages into a list, dataframe, or cache before responding.
- Use stable ordering and the documented paging API. Mutable datasets can
  shift between numbered pages; use durable IDs and deduplication/checkpoints
  as appropriate. Do not claim snapshot consistency or invent a cursor API.
- Keep durable progress and compact summaries in records. Make restarts safe
  and avoid duplicate jobs. Backend startup must not launch a full resync on
  every restart. In-process tasks/cache are not durable job execution.
- For repeated dashboards, maintain small authorized summaries or a bounded
  cache instead of recalculating from every record for every viewer.
  Long-running work needs an explicit resumable design, not more threads or
  a larger timeout. Respect provider quotas as well as Hangar's limits.

### Avoid repeating unchanged work

Before adding recurring or data-heavy work, identify what changes between
runs and estimate rows/bytes processed per run multiplied by frequency and
viewers/jobs. A bounded-memory job can still exhaust shared CPU or bandwidth.

- Separate initial backfill from routine refresh. Prefer supported watermarks,
  source revisions or changed partitions over rebuilding all history. Define
  how late arrivals, corrections and deletions invalidate prior results; never
  assume yesterday is the only mutable date. If reliable change detection is
  unavailable, use a justified reconciliation window or periodic full rebuild
  consistent with the required freshness, and make its cost explicit.
- Reuse summaries across charts/viewers only within the same authorized scope.
  Key reusable results by input revision, calculation version, normalized
  filters and access context. Invalidate affected results on relevant changes;
  presentation-only edits should not require a warehouse backfill.
- Filter and aggregate at the source where documented APIs support it. Avoid
  repeated parse/serialize/compress/decompress passes over the same data.
  Streaming bounds peak memory, not total CPU work; do not remove compression
  by replacing it with an unbounded decoded cache. Measure the expensive phase
  before changing parsers, formats or compression levels.
- Deduplicate equivalent jobs and prevent overlap across relevant workers or
  instances; a process-local lock does not coordinate Preview and live runtimes.
  Use documented coordination mechanisms, not invented lock APIs. Checkpoint
  expensive work against its input revision so retries can safely resume;
  expose a new complete generation only after validation, retaining the last
  verified result on failure. Background threads protect responsiveness but
  do not make CPU-heavy work cheaper or provide durable execution.

### Handle overload without a retry storm

- HTTP 429 `HANGAR_APP_DATA_BUSY` means data admission rejected the operation
  before its body/write was processed. HTTP 503 `HANGAR_STORAGE_BUSY` or
  `HANGAR_STORAGE_READ_TIMEOUT` means storage capacity or its deadline failed.
  For safe reads, honor `Retry-After` when available, add jitter and exponential
  backoff, and cap both attempts and elapsed time (for example, two retries).
  After that, show a recoverable error; do not silently restart the retry loop.
- HTTP 503 `HANGAR_STORAGE_READ_LIMIT` can mean the individual response or
  shared active-byte budget was exceeded. Reduce page/payload size first;
  if already small, allow only bounded delayed retries. Never retry an
  unchanged oversized response indefinitely. Reads fail, not truncate.
- HTTP 413 means the applicable body, record, source, or quota limit needs
  attention, not immediate retry. Compact or split future work appropriately;
  preserve existing data and unsaved input. Report legacy data that needs an
  authorized cleanup rather than deleting it or raising platform limits.
- A failed/aborted write response can conceal a committed mutation. Verify its
  outcome before retrying; do not blindly replay create, payment, notification,
  or other non-idempotent actions. Use idempotency only where documented.
  Do not add retry layers that multiply existing SDK/provider retries.

## Keep computation and rendering proportional

- Keep synchronous Python SDK/network calls out of async event loops: use
  plain `def` routes or explicitly offload blocking calls. Move expensive
  parsing/aggregation away from render functions and keystroke handlers; use
  a worker or backend only when the workload warrants it.
- Cache compact repeated results with TTL, entry-count and byte bounds;
  invalidate after relevant writes and coalesce concurrent misses where possible.
  A TTL alone does not bound memory, and a cache is not a place for whole tables.
  Hangar's cache is app-scoped, not automatically user-scoped:
  include the verified actor and relevant query/access context for private
  results, and recheck authorization. Do not serve one user's provider data
  from a shared cache key or cache errors indefinitely.
- Render the current page or virtualize genuinely large lists. Avoid repeated
  parsing, sorting, or nested scans per rendered row. Defer hidden charts,
  editors, previews, and expensive initialization until needed; dispose them
  when appropriate without discarding user work.
- Prefer existing runtime helpers and focused dependencies. Do not embed
  vendor bundles, whole datasets, fonts, or generated media in source to make
  an app "self-contained". Verify any lazy-import strategy in both Hangar
  Preview and the published build before claiming it reduces startup bytes.
- Prefer CSS for simple decoration. Only add Canvas/WebGL or continuous
  animation when the experience needs it; cap resolution/work, pause when
  hidden, and respect reduced motion.

## Verify the behavior, not just compilation

For a new app or a change affecting loading, data volume, media, or repeated
work, inspect the changed source and run a representative workflow. For a
small copy/style edit, keep verification proportional.

1. Inspect the largest changed files and payload shapes for encoded media,
   bundled datasets, eager full scans, request fan-out, and repeated writes.
2. With available browser/network tools, check a cold first load, the primary
   interaction, and a repeat visit using representative rows/media. Observe
   time until useful content, request count, transferred bytes, large responses,
   and long main-thread work. Check that loading page 1 does not fetch page 2,
   idle/hidden views stop unnecessary work, and polls never overlap.
3. For a slow-app fix, compare before/after under the same data and conditions.
   For a new app, choose a reasonable startup/request budget for its workflow
   and investigate oversized outliers. Platform upload/record limits are
   safety ceilings, not performance targets.
4. With fixtures or mocks, exercise multiple viewers/jobs, a slow response,
   429/503/413, and an ambiguous write outcome. Verify bounded memory/requests,
   finite retries, and retained user input; never stress-test production.
   For recurring work, compare an unchanged refresh and a single-partition
   update with initial backfill. Exercise a historical correction and an
   interrupted/resumed job; verify correct totals and no duplicated effects.
   Observe rows/bytes processed, upstream calls, elapsed time and available
   CPU/memory evidence. Explain unavoidable full rescans rather than claiming
   that small chunks alone make a job efficient.
5. Keep a compact performance contract in `design/design.md` for data-heavy
   apps: freshness and expected volume; backfill versus routine refresh;
   correction/invalidation policy; work shared across viewers; page, payload,
   cache, concurrency and job budgets; measurements and remaining gaps.
   Update it when those assumptions change, not for every small edit.
   Report actual observations and anything unmeasured. A successful compile,
   health response, or mounted preview proves neither speed nor scalability.
   The Craft preview check reports basic runtime diagnostics, not a performance
   profile; do not invent timings when measurement tools are unavailable.

Use isolated fixtures or Preview test records when available; do not seed or
modify production records or trigger external writes merely to benchmark.
## Related capabilities

- `frontend.data`
- `frontend.hangarkit`
- `backend.hangarkit`
- `backend.cache`
- `backend.integration.google_drive`
