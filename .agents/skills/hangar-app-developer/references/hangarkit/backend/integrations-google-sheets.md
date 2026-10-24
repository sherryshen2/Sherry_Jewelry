# Google Sheets integration

ID: `backend.integration.google_sheets`
Category: `backend`

Create spreadsheets and read/write Google Sheets values and sheets from backend code.

## Import

`from hangarkit.integrations import google_sheets`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `google_sheets.create_spreadsheet(title, sheets=None), get_spreadsheet(spreadsheet_id_or_url, ranges=None, include_grid_data=False, fields=None)`
- `google_sheets.get_sheet_names(...), get_sheet_id(...)`
- `google_sheets.get_values(spreadsheet_id_or_url, range_name, ...), batch_get_values(spreadsheet_id_or_url, ranges, ...)`
- `google_sheets.update_values(spreadsheet_id_or_url, range_name, values, value_input_option="RAW"), append_values(spreadsheet_id_or_url, range_name, values, ...), batch_update_values(spreadsheet_id_or_url, data, value_input_option="RAW")`
- `google_sheets.batch_update(spreadsheet_id_or_url, requests, include_spreadsheet_in_response=False), add_sheet(spreadsheet_id_or_url, title), delete_sheet(spreadsheet_id_or_url, sheet_id=None, sheet_name=None), rename_sheet(spreadsheet_id_or_url, sheet_id=None, sheet_name=None, new_title=None)`
- `google_sheets.request(method, path, **kwargs)`

## Details

Use this module for Google Sheets API workflows from backend code.

Prefer helper methods such as `get_values()`, `batch_get_values()`, and `update_values()` over raw `request()` calls. The helpers route through the Google Sheets connector correctly and keep spreadsheet/range URL details out of app code.

Configure the app integration before publishing:

```json
{
  "integrations": {
    "google_sheets": { "auth_mode": "user" }
  }
}
```

Use user auth mode when the sheet should be read with the current runtime user's linked Wingman/Google access. A Hangar session cookie alone is only app identity; it does not authorize Google Sheets connector calls. If every user should read the same sheet without bringing their own Wingman JWT, use owner-token app auth instead:

```json
{
  "integrations": {
    "google_sheets": {      "auth_mode": "app",
      "app_provider": "owner_token"
    }
  }
}
```

Hangar derives the Wingman owner email from the app owner in owner-token mode.

### Values and sheet-management workflow

All helpers accept either a spreadsheet ID or its Google Sheets URL. Values are two-dimensional rows; for example, `[["Name", "Status"], ["Alice", "Ready"]]`. `range_name` uses A1 notation.

```python
from hangarkit.integrations import google_sheets

sheet = google_sheets.create_spreadsheet("Launch tracker", sheets=["Tasks"])
spreadsheet_id = sheet["spreadsheetId"]
google_sheets.update_values(spreadsheet_id, "Tasks!A1:B2", [["Task", "State"], ["Ship", "Ready"]])
google_sheets.append_values(spreadsheet_id, "Tasks!A:B", [["Validate", "Queued"]])
```

`batch_update_values()` requires a non-empty list of Google Values API data objects; `batch_update()` requires a non-empty list of Google Sheets API request objects. `delete_sheet()` and `rename_sheet()` require either `sheet_id` or `sheet_name`; renaming also requires `new_title`.

For raw requests, pass Sheets API paths or absolute Google API URLs. `google_sheets.request("GET", "/v4/spreadsheets/{id}/values/Sheet1!A1:C10")` and `google_sheets.request("GET", "https://sheets.googleapis.com/v4/spreadsheets/{id}/values/Sheet1!A1:C10")` are valid. Do not route Sheets reads through generic Google connector paths such as `/api/hangar/connectors/user/google/v4/...` or `/api/hangar/connectors/user/google/sheets/v4/...`; those become Google 404s. HangarKit maps Google Sheets traffic to the `google_domain/sheets` connector route.
## Quick examples

- `rows = google_sheets.get_values(spreadsheet_id, "Sheet1!A1:C10")`

## Related capabilities

- `backend.integrations`
