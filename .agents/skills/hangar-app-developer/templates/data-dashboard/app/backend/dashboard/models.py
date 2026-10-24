from dataclasses import dataclass


@dataclass
class SourceDataset:
    name: str
    source_type: str
    rows: list[dict]
    columns: list[str]

    def payload(self) -> dict:
        return {
            "name": self.name,
            "source_type": self.source_type,
            "rows": self.rows,
            "columns": self.columns,
            "row_count": len(self.rows),
        }
