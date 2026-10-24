# $hangarkit frontend helpers

ID: `frontend.hangarkit`
Category: `frontend`

App-scoped helpers for backend calls, assets, external proxying, auth, low-level storage, cache, preferences, and prefix-safe navigation.

## Import

`import { api, asset, proxy, auth, table, storage, cache, nav, appPath, localPath, navigate, preferences, theme, language } from '$hangarkit'`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `api.get(path), api.post(path, body), api.patch(path, body), api.delete(path), api.request(path, options)`
- `asset(filename, { thumb?, download? })`
- `proxy(url, options), proxy.json(url), proxy.text(url), proxy.url(url)`
- `auth.currentUser(), auth.requireUser(), auth.logout()`
- `appPath(path), localPath(path), navigate(path, options?)`
- `nav.href(path), nav.path(path), nav.localPath(path), nav.navigate(path), nav.push(path), nav.replace(path)`
- `table(name), storage.table(name)`
- `cache.get(key), cache.has(key), cache.set(key, value, { ttl? }), cache.delete(key), cache.remember(key, ttl, loader)`

## Details

Use `$hangarkit` from frontend app code. These helpers preserve app scoping and work under optional `HANGAR_APP_PREFIX` and `/apps/:slug` routing.

Prefer these helpers over hardcoded `/hangar`, `/apps/:slug`, project IDs, direct data routes, or direct asset routes.

Asset bytes are served from the owning Hangar VM's persistent disk after
Hangar authorization. Keep using `asset()` and app-scoped uploads; do not
construct public filesystem URLs or depend on PocketBase/MySQL file endpoints.

The current disk server generates only the `640x360` thumbnail preset (cropped
to fit). Other `thumb` values return the original file; unsupported/oversized
images can also fall back to the original. Do not assume arbitrary thumbnail
sizes reduce transferred bytes. For a different aspect ratio, preserve the
original or upload a resized derivative and keep its filename separately.

As a temporary ALB routing fix, `api.url()` and `api.get/post/patch/delete/request()`
use the fixed base `https://wingman.shopee.io/hangar`, keeping the app slug or
preview path and replacing the node's path prefix with `/hangar`. Browser
requests still include credentials by default. Other helpers, including data,
cache, assets, auth, and navigation, keep their existing address behavior.
Published HTML embeds the SDK, so existing published apps keep their old API
addresses until explicitly republished after the platform update.

Important for local development: `$hangarkit` is a virtual module provided by Hangar's build/runtime pipeline. It is not expected to resolve in a plain local Svelte/Vite project unless that project is being built by Hangar.
## Quick examples

- `const status = await api.get('/health')`
- `<img src={asset(product.image, { thumb: '640x360' })} alt={product.name} />`
- `<a href={nav.href('/settings')}>Settings</a>`

## Related capabilities

- `frontend.data`
- `frontend.content`
- `runtime.routing`
- `backend.hangarkit`
