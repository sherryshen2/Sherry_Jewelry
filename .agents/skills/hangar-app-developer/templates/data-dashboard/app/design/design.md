# Data dashboard

## Product model

The dashboard accepts multiple schema-unknown sources at once. A datasource is a named, typed input: local demo data, CSV upload, Google Sheet range, or Datasuite API response. A record is a normalized row belonging to one datasource; `_source` and `_source_row` preserve provenance when records are combined.

## Pages

- **Home** is an immediate, presentation-ready overview. It starts with the local demo datasource and shows summary metrics plus line, donut, and bar charts. Keep search and detailed filters off this page.
- **Data sources** inventories connected sources, their type, record count, and discovered fields. Users can remove a source here.
- **Records** is the exploration workspace for search, filtering, aggregation controls, and the raw table.
- **Configuration** is the only page for adding or changing data connections. It supports local demo data, multiple CSV files, a Google Sheet URL/ID and A1 range, and Datasuite query parameters.

## Design direction

Use a calm analytical workspace: light canvas, crisp cards, one purple accent, dense but legible labels, and modest rounded corners. The primary navigation is persistent. Data source identity should be visible in every source list. Prefer semantic visualizations selected from inferred fields: a trend line for ordered period-like fields, a donut for composition, and bars for ranking. Do not require a known schema to render the first dashboard.

## Engineering guardrails

Keep source adapters in `backend/dashboard/` and HTTP handling in `backend/routers/dashboard.py`. Datasuite secrets remain server-side. Google Sheets is accessed only with the HangarKit integration in backend code. Keep frontend analysis pure and schema-agnostic in `frontend/src/lib/` so future source types can reuse it.
