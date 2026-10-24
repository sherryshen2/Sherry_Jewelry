# Data dashboard

This native Hangar dashboard uses Svelte for the interactive UI and FastAPI for source loading. It starts with local demo data so useful graphs render immediately, and it supports CSV, Google Sheets through HangarKit, and Datasuite in the same browser session.

## Structure

- `frontend/src/App.svelte` owns the four page-level views: Home, Data sources, Records, and Configuration.
- `frontend/src/lib/sample-data.ts` contains the local demo datasource used by a new dashboard.
- `frontend/src/lib/data.ts` is the schema-agnostic client-side analysis layer: unioning, filtering, numeric inference, and aggregation.
- `frontend/src/components/` contains reusable source configuration, chart, and table UI.
- `backend/routers/dashboard.py` exposes one endpoint per source type.
- `backend/dashboard/` contains source adapters and normalization. New source types belong here.

## Secrets and integrations

Google Sheets uses the configured `google_sheets` HangarKit integration.

Datasuite credentials are server-side secrets only:

- `DATASUITE_APP_KEY`
- `DATASUITE_APP_SECRET`
- `DATASUITE_SYSTEM_NAME`
- `DATASUITE_END_USER`

The user supplies the Datasuite API name, version, scope, and JSON expression parameters on the Configuration page. Credentials never enter browser code or API responses.
