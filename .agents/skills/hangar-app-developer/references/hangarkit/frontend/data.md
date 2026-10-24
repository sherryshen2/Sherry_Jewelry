# $data persistent realtime collections

ID: `frontend.data`
Category: `data`

Reactive app-scoped database access for generated frontend apps.

## Import

`import data from '$data'`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `data.collection.subscribe(callback, params?)`
- `data.collection.list(params?), page(params?), get(id, params?)`
- `data.collection.create(record), update(id, patch), delete(id)`
- `data.collection.createMany(records), deleteMany(ids)`

## Details

Use `$data` for persistent UI data such as todos, posts, products, notes, settings, and records users expect to survive refreshes.

Collections are created by the agent with `create_data_file` or through the external API table endpoints, then exposed under `data.<collection>`.

Collection reads are always paginated. `perPage` defaults to 100 and has a legacy-compatible maximum of 500; prefer pages of 100 or fewer for new apps, especially when records are large. Simple filters such as `status = "open"`, `score >= 10`, and `done = true` are evaluated by the configured storage backend; sorts accept up to five comma-separated fields such as `-updated,title`. Unsupported filter or sort expressions are rejected instead of falling back to an in-memory full-table scan.

`createMany(records)` inserts 1-100 JSON records in one atomic batch and returns the created rows. `deleteMany(ids)` deletes 1-100 distinct record IDs atomically and returns the deleted IDs; a missing ID rejects the batch. These methods never wipe the whole table. Use `get(id)` and the returned `id` for precise row selection; list positions are not stable identifiers. Batch methods do not upload browser `File` objects; use single-record `create` for files.

Each created or updated record is limited to 10 MiB of JSON data. Store large binary content as app assets and keep only the asset filename and compact metadata in the record.

The record limit is a safety ceiling, not a target. Do not store uploaded media
as base64/data URLs or byte arrays in text/JSON fields. For growing lists, use
`page()` with visible pagination rather than fetching every page at startup;
`list()` and `subscribe()` also return bounded pages, not complete collections.
Follow `workflow.app_performance` for media, request, and rendering choices.

Persistent table data has a 5 GiB logical JSON quota per app by default. Platform admins can set a per-app quota from the Data Monitor. Hangar allows up to 1% above the configured quota, capped at 16 MiB; growing writes return HTTP 413 when cached usage would exceed this allowance. Usage accounting is best-effort and persists in the background without serializing app writes. Concurrent writes, a cold cache, or unavailable counters can temporarily exceed the quota; counter failures do not fail record writes. Deleting records and updates that do not grow stored JSON remain allowed even above the limit. The quota measures stored JSON data, not backend memory or uploaded asset files.

Call `subscribe()` directly at top level in Svelte app code. Do not wrap it in `onMount()` or `$effect()`.

`subscribe()` loads the initial collection records in both live apps and Craft preview, then continues to receive runtime updates. In Craft preview, parent-frame data may render immediately, but `subscribe()` still reconciles with the preview runtime data route so stale or empty builder state cannot hide or overwrite records that exist in app storage.

For user uploads, create the collection with `file` or `files` fields, then pass browser `File` objects directly to `create(record)` or `update(id, patch)`. HangarKit automatically sends multipart form data, stores the uploaded asset in the current app, and writes the returned asset filename into the data record.

```svelte
<script>
  import data from '$data'
  import { asset } from '$hangarkit'

  let title = $state('')
  let file = $state(null)
  let saved = $state(null)

  async function submit() {
    saved = await data.submissions.create({ title, attachment: file })
  }
</script>

<input bind:value={title} />
<input type="file" onchange={(event) => file = event.currentTarget.files?.[0] ?? null} />
<button onclick={submit}>Upload</button>

{#if saved?.attachment}
  <a href={asset(saved.attachment)}>Open upload</a>
{/if}
```

File field values in records are asset filenames, not raw bytes or public URLs. Use `asset(filename)` in frontend code to render or link to the uploaded file.

Important for local development: `$data` is a virtual module injected by Hangar. It will not exist in a user-local app folder outside Hangar's compiler/runtime.
## Quick examples

- `data.todos.subscribe(items => { todos = items; loading = false })`
- `await data.todos.create({ title: 'New task', done: false })`
- `await data.submissions.create({ title, attachment: file })`

## Related capabilities

- `workflow.app_performance`
