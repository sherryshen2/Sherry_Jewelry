# Python backend cache

ID: `backend.cache`
Category: `backend`

App-scoped ephemeral cache helpers for backend code.

## Import

`from hangarkit import cache`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `cache.get(key)`
- `cache.has(key)`
- `cache.set(key, value, ttl=None)`
- `cache.delete(key)`
- `cache.remember(key, ttl, loader)`

## Details

Use backend `cache` for app-scoped values that are safe to lose and useful to avoid repeated expensive work.

Do not use cache as durable storage. Use `hangarkit.table()` or frontend `$data` for durable app records.
## Quick examples

- `cache.set("report", result, ttl=300)`
- `value = cache.remember("summary", 60, lambda: build_summary())`

## Related capabilities

- `backend.hangarkit`
- `runtime.backend`
