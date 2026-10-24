# Local Python HangarKit SDK

ID: `backend.local_python_sdk`
Category: `backend`

Local development package for running backend/main.py with live-compatible Python hangarkit imports and app-scoped mock routes.

## Import

`from hangarkit import ctx, table, app_url, api_url, asset_url, cache`

`from hangarkit.integrations import jira`

`from hangarkit.platform import seatalk`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `hangarkit dev --slug app-slug`
- `hangarkit dev --slug app-slug --connect http://127.0.0.1:5173`
- `WINGMAN_TOKEN`
- `HANGARKIT_WINGMAN_TOKEN`
- `~/.wingman/auth.json`
- `/apps/:slug/api/*`
- `/apps/:slug/data/*`
- `/apps/:slug/assets/*`

## Details

Use the local Python SDK when developing a Hangar backend outside the live Hangar runner. The SDK package is stored under `packages/hangarkit-python-sdk` and publishes as the Python distribution `shopee_hangarkit`. It still provides the Python module `hangarkit` so user app code matches live Hangar.

Local app code should look the same as live app code:

```python
from fastapi import APIRouter
from hangarkit import ctx, table, app_url

router = APIRouter()

@router.get("/health")
def health():
    return {
        "app": ctx.app_slug,
        "user": ctx.user_email,
        "profile": ctx.current_user,
        "avatar_url": ctx.user_avatar_url,
        "home": app_url("/"),
        "notes": table("notes").list(),
    }
```

`ctx.current_user`, `ctx.user_name`, and `ctx.user_avatar_url` use the same profile contract as the live backend. In local mock mode, the profile has the configured development ID and email; connected mode receives the signed-in Hangar profile.

Run a backend from an app folder with:

```bash
pip install --index-url https://pypi.shopee.io/simple "shopee_hangarkit[dev]"
hangarkit dev --slug notes
```

The local dev gateway preserves the live single-domain path model:

```txt
http://127.0.0.1:8787/apps/notes/api/*
http://127.0.0.1:8787/apps/notes/data/*
http://127.0.0.1:8787/apps/notes/assets/*
```

Mock mode is the default and stores data/cache files under `.hangarkit/local/:slug`. Connected mode points helpers at a running Hangar origin:

```bash
hangarkit dev --slug notes --connect http://127.0.0.1:5173
```

The SDK includes the same public `hangarkit.integrations` and `hangarkit.platform` modules as live Hangar. In local SDK/dev mode, integration and current-user platform helpers may use the current owner/editor Wingman token to call Wingman directly:

```bash
export WINGMAN_TOKEN="<token>"
```

The SDK resolves a local Wingman token in this order:

1. `WINGMAN_TOKEN`
2. `HANGARKIT_WINGMAN_TOKEN`
3. `~/.wingman/auth.json`, using `accessToken` only when `expiresAt` is still valid

```python
from hangarkit.integrations import jira
from hangarkit.platform import seatalk

issue = jira.get_issue("SPB-61060")
groups = seatalk.list_groups(query="release")
```

In live Hangar, integrations use platform-owned credentials selected by the app integration config and the current Hangar session. Live app frontend/backend code does not receive raw Wingman user tokens.

Do not add local-only branches to app code. The local SDK is for development; live Hangar still injects its own runtime package and starts the backend through the platform runner.

If `backend/requirements.txt` includes `shopee_hangarkit` or `shopee_hangarkit[dev]` for local editor/test compatibility, Hangar strips that requirement during live backend deployment because the live runner injects its own `hangarkit` package. App code should still import `hangarkit`, not `shopee_hangarkit`.

The local SDK covers core backend helpers for context, URLs, app data, cache, assets, mock email, mock short links, public integration helpers, and the narrow platform helpers. Data/cache/email/short-link helpers stay mocked by default so local tests do not mutate production app state unless connected mode is explicitly configured.
## Quick examples

- `pip install --index-url https://pypi.shopee.io/simple "shopee_hangarkit[dev]"`
- `export WINGMAN_TOKEN=<token>`
- `hangarkit dev --slug notes`

## Related capabilities

- `backend.hangarkit`
- `runtime.routing`
