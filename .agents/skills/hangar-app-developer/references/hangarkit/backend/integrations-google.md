# Google integration

ID: `backend.integration.google`
Category: `backend`

Call Google APIs through Hangar integration auth when a provider-specific helper does not exist yet.

## Import

`from hangarkit.integrations import google`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `google.request(method, path, **kwargs)`
- `google.get(path, **kwargs), post(path, **kwargs), put(path, **kwargs), patch(path, **kwargs), delete(path, **kwargs)`

## Details

Use this module for raw Google API calls when HangarKit does not yet expose a product-specific helper. Prefer product modules such as `google_drive`, `google_docs`, `google_mail`, or `google_sheets` when they fit the workflow.

Relative paths route through the generic Wingman Google connector. Absolute URLs must target `*.googleapis.com`; Hangar maps domains such as `drive.googleapis.com` through the Google domain connector.
## Quick examples

- `profile = google.get("/oauth2/v3/userinfo")`
- `discovery = google.get("https://www.googleapis.com/discovery/v1/apis")`

## Related capabilities

- `backend.integrations`
- `backend.integration.google_drive`
- `backend.integration.google_sheets`
