import json
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def _unique_name(name: str, used: set[str]) -> str:
    candidate = name or "Column"
    suffix = 2
    while candidate in used:
        candidate = f"{name or 'Column'} ({suffix})"
        suffix += 1
    used.add(candidate)
    return candidate


def headers_from_row(values: list[Any]) -> list[str]:
    used: set[str] = set()
    return [_unique_name(str(value or "").strip() or f"Column {index + 1}", used) for index, value in enumerate(values)]


def rows_from_values(values: list[list[Any]]) -> list[dict[str, Any]]:
    if not values:
        return []
    headers = headers_from_row(values[0])
    return [{header: row[index] if index < len(row) else None for index, header in enumerate(headers)} for row in values[1:]]


def flatten_record(record: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten nested API objects without assuming a provider-specific schema."""
    output: dict[str, Any] = {}
    for key, value in record.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            output.update(flatten_record(value, name))
        elif isinstance(value, (list, tuple, set)):
            output[name] = json.dumps(value, default=str, ensure_ascii=False)
        else:
            output[name] = value
    return output


def json_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (date, datetime, Decimal)):
        return str(value)
    return str(value)


def source_rows(records: Iterable[Mapping[str, Any]], source_name: str) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    columns: list[str] = []
    known_columns: set[str] = set()
    for index, record in enumerate(records, start=1):
        row = {key: json_value(value) for key, value in flatten_record(record).items()}
        row["_source"] = source_name
        row["_source_row"] = index
        for column in row:
            if column not in known_columns:
                known_columns.add(column)
                columns.append(column)
        rows.append(row)
    return rows, columns
