from .models import SourceDataset
from .normalize import rows_from_values, source_rows


def read_google_sheet(spreadsheet: str, range_name: str) -> SourceDataset:
    """Read a sheet through HangarKit without assuming its headers or fields."""
    if not spreadsheet.strip():
        raise ValueError("Spreadsheet URL or ID is required")
    from hangarkit.integrations import google_sheets

    result = google_sheets.get_values(spreadsheet, range_name or "Sheet1!A:ZZ")
    source_name = "Google Sheets"
    rows, columns = source_rows(rows_from_values(result.get("values") or []), source_name)
    return SourceDataset(name=source_name, source_type="google_sheets", rows=rows, columns=columns)
