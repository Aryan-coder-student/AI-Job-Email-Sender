from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from app.modules.excel.validator import validate_excel_parser_config
from setting import EXCEL_COLUMN_ALIASES


@dataclass(frozen=True)
class ExcelParserConfig:
    """Controls how uploaded or remote Excel files are read."""

    sheet_count: int | None = 1
    max_rows: int | None = None
    max_empty_ratio: float | None = 0.9
    header_row: int = 1
    sheet_names: tuple[str, ...] = ()
    column_aliases: Mapping[str, tuple[str, ...]] = field(
        default_factory=lambda: EXCEL_COLUMN_ALIASES
    )
    download_timeout_seconds: int = 20
    max_download_bytes: int = 10 * 1024 * 1024

    def validate(self) -> None:
        validate_excel_parser_config(self)
