from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CompanyImportRow:
    row_id: str
    source_sheet: str
    source_row: int
    normalized: dict[str, Any]
    raw_data: dict[str, Any]
    issues: list[str]

    @property
    def is_valid(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_id": self.row_id,
            "source_sheet": self.source_sheet,
            "source_row": self.source_row,
            "normalized": self.normalized,
            "raw_data": self.raw_data,
            "issues": self.issues,
            "is_valid": self.is_valid,
        }


@dataclass(frozen=True)
class CompanyImportPreview:
    import_id: str
    filename: str
    rows: list[CompanyImportRow]

    @property
    def total_rows(self) -> int:
        return len(self.rows)

    @property
    def valid_rows(self) -> int:
        return sum(1 for row in self.rows if row.is_valid)

    @property
    def invalid_rows(self) -> int:
        return self.total_rows - self.valid_rows

    def valid_company_records(self) -> list[dict[str, Any]]:
        return [row.normalized for row in self.rows if row.is_valid]

    def to_dict(self) -> dict[str, Any]:
        return {
            "import_id": self.import_id,
            "filename": self.filename,
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "invalid_rows": self.invalid_rows,
            "rows": [row.to_dict() for row in self.rows],
        }
