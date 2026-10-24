# Platform Toolverse helpers

ID: `backend.platform.toolverse`
Category: `backend`

Look up API ownership, identifiers, and encoded extinfo with no app credentials or generic Toolverse client.

## Import

`from hangarkit.platform import toolverse`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `toolverse.search_api_owner(api, timeout=30)`
- `toolverse.id_finder(id, env=None, region=None, timeout=30)`
- `toolverse.ext_decode(input, timeout=30)`

## Details

Use `hangarkit.platform.toolverse` for the supported, read-only Toolverse lookups. It does not expose a generic `request()` method and does not require an app-level Toolverse token or Seatalk configuration.

`search_api_owner(api)` accepts an HTTP URL/path, SPEX path, IP, or service name and returns the raw Toolverse ownership result. `id_finder(id, env=None, region=None)` accepts an identifier and optional environment/region filters. `ext_decode(input)` decodes Toolverse-supported extinfo or extra-data values.

These helpers use the signed-in runtime user's authorization through Hangar's server-side proxy. Hangar requests normal integration approval for non-owner users and sends requests only to the three allowlisted Toolverse read endpoints. Returned values preserve the Toolverse BE response shape, including its `error_code` and `error_message` fields when present.

```python
from hangarkit.platform import toolverse

owners = toolverse.search_api_owner("/api/v4/checkout/get")
matches = toolverse.id_finder("123456", env="live", region="sg")
decoded = toolverse.ext_decode("encoded-value")
```
## Quick examples

- `owners = toolverse.search_api_owner("/api/v4/checkout/get")`
- `matches = toolverse.id_finder("123456", env="live", region="sg")`
- `decoded = toolverse.ext_decode("encoded-value")`

## Related capabilities

- `backend.hangarkit`
- `backend.platform.seatalk`
