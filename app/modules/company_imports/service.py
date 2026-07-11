from __future__ import annotations

import csv
import json
import uuid
from io import StringIO
from pathlib import Path
from typing import Any

from app.core.exceptions import InvalidExcelError
from app.modules.company_imports.model import CompanyImportPreview, CompanyImportRow
from app.modules.company_imports.repository import CompanyImportRepository
from app.modules.excel.config import ExcelParserConfig
from app.modules.excel.parser import ParsedExcelRow, ParsedExcelWorkbook, parse_excel_from_upload
from app.modules.excel.sources import parse_excel_from_url
from app.modules.excel.utils import build_alias_lookup, build_headers, normalize_data, row_to_dict

SUPPORTED_COMPANY_IMPORT_EXTENSIONS = {".csv", ".json", ".xlsx", ".xlsm", ".xltx", ".xltm"}
DEFAULT_COMPANY_ALIAS_LOOKUP = build_alias_lookup(ExcelParserConfig())


def preview_company_import(
    *,
    content: bytes,
    filename: str,
    output_dir: Path,
    config: ExcelParserConfig | None = None,
) -> dict[str, Any]:
    preview = CompanyImportPreview(
        import_id=uuid.uuid4().hex,
        filename=filename,
        rows=parse_company_import_rows(content=content, filename=filename, config=config),
    )
    CompanyImportRepository(output_dir=output_dir).save_preview(preview)
    return preview.to_dict()


def preview_company_import_from_url(
    *,
    url: str,
    output_dir: Path,
    config: ExcelParserConfig | None = None,
) -> dict[str, Any]:
    workbook = parse_excel_from_url(url, config=config or ExcelParserConfig())
    preview = CompanyImportPreview(
        import_id=uuid.uuid4().hex,
        filename=workbook.filename or url,
        rows=_excel_workbook_to_import_rows(workbook),
    )
    CompanyImportRepository(output_dir=output_dir).save_preview(preview)
    return preview.to_dict()


def parse_company_import_rows(*, content: bytes, filename: str, config: ExcelParserConfig | None = None) -> list[CompanyImportRow]:
    suffix = _supported_suffix(filename)
    if suffix == ".csv":
        return _parse_csv_rows(content=content, filename=filename)
    if suffix == ".json":
        return _parse_json_rows(content=content, filename=filename)
    return _parse_excel_rows(content=content, filename=filename, config=config)


def _supported_suffix(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in SUPPORTED_COMPANY_IMPORT_EXTENSIONS:
        return suffix

    supported = ", ".join(sorted(SUPPORTED_COMPANY_IMPORT_EXTENSIONS))
    raise InvalidExcelError(f"Unsupported company file type. Use one of: {supported}.")


def _parse_excel_rows(*, content: bytes, filename: str, config: ExcelParserConfig | None = None) -> list[CompanyImportRow]:
    workbook = parse_excel_from_upload(content, filename=filename, config=config)
    return _excel_workbook_to_import_rows(workbook)


def _excel_workbook_to_import_rows(workbook: ParsedExcelWorkbook) -> list[CompanyImportRow]:
    return [_excel_row_to_import_row(row) for row in workbook.rows]


def _excel_row_to_import_row(row: ParsedExcelRow) -> CompanyImportRow:
    normalized = {
        **row.normalized,
        "source_sheet": row.sheet_name,
        "source_row": row.row_number,
        "raw_data": row.data,
    }
    return _build_import_row(
        source_sheet=row.sheet_name,
        source_row=row.row_number,
        normalized=normalized,
        raw_data=row.data,
    )


def _parse_csv_rows(*, content: bytes, filename: str) -> list[CompanyImportRow]:
    reader = csv.reader(StringIO(content.decode("utf-8-sig")))
    header_values = next(reader, None)
    if not header_values:
        raise InvalidExcelError("CSV file does not contain a header row.")

    headers = build_headers(tuple(header_values))
    source_sheet = Path(filename).stem or "csv"
    rows: list[CompanyImportRow] = []
    for row_number, values in enumerate(reader, start=2):
        if _is_blank_row(values):
            continue

        rows.append(
            _csv_row_to_import_row(
                headers=headers,
                source_sheet=source_sheet,
                source_row=row_number,
                values=tuple(values),
            )
        )
    return rows


def _csv_row_to_import_row(
    *,
    headers: list[str],
    source_sheet: str,
    source_row: int,
    values: tuple[Any, ...],
) -> CompanyImportRow:
    raw_data = row_to_dict(headers, values)
    normalized = _normalize_company_data(raw_data)
    return _build_import_row(
        source_sheet=source_sheet,
        source_row=source_row,
        normalized=normalized,
        raw_data=raw_data,
    )


def _parse_json_rows(*, content: bytes, filename: str) -> list[CompanyImportRow]:
    payload = json.loads(content.decode("utf-8"))
    if not isinstance(payload, list):
        raise InvalidExcelError("JSON company import must be a list of objects.")

    source_sheet = Path(filename).stem or "json"
    rows: list[CompanyImportRow] = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise InvalidExcelError(f"JSON company row {index} must be an object.")

        rows.append(
            _json_row_to_import_row(
                source_sheet=source_sheet,
                source_row=index,
                payload=item,
            )
        )
    return rows


def _json_row_to_import_row(
    *,
    source_sheet: str,
    source_row: int,
    payload: dict[str, Any],
) -> CompanyImportRow:
    normalized = _normalize_company_data(payload) or payload
    return _build_import_row(
        source_sheet=source_sheet,
        source_row=source_row,
        normalized=normalized,
        raw_data=payload,
    )


def _normalize_company_data(data: dict[str, Any]) -> dict[str, Any]:
    return normalize_data(data, DEFAULT_COMPANY_ALIAS_LOOKUP)


def _is_blank_row(values: list[str]) -> bool:
    return all(not str(value or "").strip() for value in values)


def _build_import_row(
    *,
    source_sheet: str,
    source_row: int,
    normalized: dict[str, Any],
    raw_data: dict[str, Any],
) -> CompanyImportRow:
    return CompanyImportRow(
        row_id=f"{source_sheet}:{source_row}",
        source_sheet=source_sheet,
        source_row=source_row,
        normalized=normalized,
        raw_data=raw_data,
        issues=_validate_company_row(normalized),
    )


def _validate_company_row(row: dict[str, Any]) -> list[str]:
    if str(row.get("company_name") or "").strip():
        return []

    return ["Company name is required."]
