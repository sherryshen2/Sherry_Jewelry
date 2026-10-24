# PMP integration

ID: `backend.integration.pmp`
Category: `backend`

Call PMP APIs from backend code with the configured user or app-level integration auth.

## Import

`from hangarkit.integrations import pmp`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `pmp.client()`
- `pmp.request(method, path, params=None, json=None, data=None, headers=None, timeout=30)`
- `pmp.get(path, **kwargs), pmp.post(path, **kwargs), pmp.put(path, **kwargs), pmp.patch(path, **kwargs), pmp.delete(path, **kwargs)`

## Details

Use this module for PMP backend calls. The runtime chooses the configured integration auth mode: user proxy auth, app owner-token proxy auth, or app service-token direct auth.

For service-token mode, Hangar sends the fixed app credential as an `Authorization: Bearer ...` header to the configured PMP base URL.

This is a backend runtime helper injected by Hangar. It is not a local Python package in a plain dev environment.
## Quick examples

- `detail = pmp.get("/api/example", params={"id": item_id})`
- `created = pmp.post("/api/example", json={"name": name})`

## Related capabilities

- `backend.integrations`
- `backend.integration.platform`
