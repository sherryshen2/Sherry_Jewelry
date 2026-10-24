SAMPLE_VALUES = [
    ["Month", "Team", "Revenue", "Pipeline", "Status"],
    ["Jan", "Platform", "12500", "20000", "Closed"],
    ["Jan", "Creator", "8300", "12000", "Closed"],
    ["Feb", "Platform", "15400", "24000", "Closed"],
    ["Feb", "Creator", "9700", "14500", "Closed"],
    ["Mar", "Platform", "18200", "26000", "Open"],
    ["Mar", "Creator", "12100", "18000", "Open"],
]


def read_values(source):
    spreadsheet = str(source.get("spreadsheet_url") or "").strip()
    range_name = str(source.get("range_name") or "").strip() or "Sheet1!A1:Z100"
    if not spreadsheet:
        return SAMPLE_VALUES

    from hangarkit.integrations import google_sheets

    result = google_sheets.get_values(spreadsheet, range_name)
    return result.get("values") or []
