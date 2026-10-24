# Platform short links

ID: `backend.short_url`
Category: `backend`

Generate platform short links from app backend code and let Hangar maintain the review record.

## Import

`from hangarkit import short_url`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `short_url.generate(title, real_url, expire_days=30)`
- `short_url.generate(title, real_url, expire_time_minutes=60)`
- `short_url.generate_short_url(title, real_url, ...)`
- `short_url.records(page=1, per_page=50)`
- `short_url.list_records(page=1, per_page=50)`

## Details

Use `short_url.generate()` in backend code when the app needs a shareable platform short link.

Hangar calls the platform short-link service, derives the operator from the real Hangar runtime user when present or the app identity otherwise, and stores a Hangar-owned record for admin review.

Do not call the short-link service directly from frontend code. Do not add Wingman user tokens for this platform-provided API.

Important for local development: `hangarkit.short_url` is injected by Hangar in deployed/backend runtime. It will not be available in a normal local Python environment.
## Quick examples

- `result = short_url.generate("Runbook", "https://example.com/runbook", expire_days=30)`
- `return {"short_url": result["short_url"]}`

## Related capabilities

- `backend.hangarkit`
- `runtime.backend`
