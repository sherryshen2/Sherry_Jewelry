# SPACE integration

ID: `backend.integration.space`
Category: `backend`

Call SPACE APIs through the default SPACE proxy or a specific SPACE domain proxy.

## Import

`from hangarkit.integrations import space`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `space.request(method, path, **kwargs)`
- `space.domain_request(domain, method, path, **kwargs)`
- `space.get(path, **kwargs), post(path, **kwargs), put(path, **kwargs), patch(path, **kwargs), delete(path, **kwargs)`

## Details

Use this module for SPACE API calls from backend code. It supports both the normal SPACE proxy and domain-specific SPACE proxy behavior.

Prefer `space.get(...)` or `space.request(...)` for the default
`https://space.shopee.io` host. `domain_request` accepts either a short SPACE
label such as `space`, `config`, or `space.test`, or its full `*.shopee.io`
hostname. Both forms select the same host in user, owner-account, and pasted
SPACE-token modes; Hangar translates the domain for the selected proxy.
Pass a hostname or label only, not a URL, port, or path.
## Quick examples

- `result = space.get("/api/some/path")`
- `result = space.domain_request("space.shopee.io", "GET", "/api/some/path")`

## Related capabilities

- `backend.integrations`
