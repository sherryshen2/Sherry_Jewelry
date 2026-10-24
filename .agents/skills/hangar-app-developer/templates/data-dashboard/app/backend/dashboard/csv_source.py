from io import BytesIO

import pandas as pd

from .models import SourceDataset
from .normalize import source_rows


def read_csv_bytes(name: str, content: bytes) -> SourceDataset:
    """Parse one browser upload while preserving arbitrary CSV columns."""
    try:
        frame = pd.read_csv(BytesIO(content))
    except UnicodeDecodeError:
        frame = pd.read_csv(BytesIO(content), encoding="latin-1")
    records = frame.where(frame.notna(), None).to_dict(orient="records")
    source_name = f"CSV · {name}"
    rows, columns = source_rows(records, source_name)
    return SourceDataset(name=source_name, source_type="csv", rows=rows, columns=columns)
