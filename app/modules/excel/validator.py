from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.core.exceptions import InvalidExcelError


SUPPORTED_EXTENSIONS = {".xlsx", ".xlsm", ".xltx", ".xltm"}


def validate_excel_parser_config(config: Any) -> None:
    if config.sheet_count is not None and config.sheet_count < 1:
        raise ValueError("sheet_count must be at least 1, or None for all sheets.")

    if config.max_rows is not None and config.max_rows < 1:
        raise ValueError("max_rows must be at least 1, or None for all populated rows.")

    if config.max_empty_ratio is not None and not 0 < config.max_empty_ratio <= 1:
        raise ValueError("max_empty_ratio must be greater than 0 and less than or equal to 1.")

    if config.header_row < 1:
        raise ValueError("header_row must be at least 1.")

    if config.download_timeout_seconds < 1:
        raise ValueError("download_timeout_seconds must be at least 1.")

    if config.max_download_bytes < 1:
        raise ValueError("max_download_bytes must be at least 1.")


def validate_excel_filename(filename: str | None) -> None:
    if not filename:
        return

    suffix = Path(filename).suffix.lower()

    if suffix and suffix not in SUPPORTED_EXTENSIONS:
        raise InvalidExcelError(
            "Unsupported Excel file type. Use .xlsx, .xlsm, .xltx, or .xltm."
        )


def validate_excel_url(url: str) -> None:
    parsed_url = urlparse(url)

    if parsed_url.scheme not in {"http", "https"}:
        raise InvalidExcelError("Excel URL must start with http:// or https://.")
