from __future__ import annotations

from typing import Any, TYPE_CHECKING
from urllib.parse import urlparse

from app.core.exceptions import InvalidExcelError
from app.modules.excel.config import ExcelParserConfig

if TYPE_CHECKING:
    from openpyxl.worksheet.worksheet import Worksheet


def select_sheets(
    worksheets: list[Worksheet],
    config: ExcelParserConfig,
) -> list[Worksheet]:
    if config.sheet_names:
        sheet_by_name = {sheet.title: sheet for sheet in worksheets}
        missing_sheets = [
            sheet_name
            for sheet_name in config.sheet_names
            if sheet_name not in sheet_by_name
        ]

        if missing_sheets:
            raise InvalidExcelError(f"Missing sheets: {', '.join(missing_sheets)}")

        return [sheet_by_name[sheet_name] for sheet_name in config.sheet_names]

    if config.sheet_count is None:
        return worksheets

    return worksheets[: config.sheet_count]


def build_headers(values: tuple[Any, ...]) -> list[str]:
    headers: list[str] = []
    seen: dict[str, int] = {}

    for index, value in enumerate(values, start=1):
        header = normalize_key(value) if value is not None else ""
        header = header or f"column_{index}"
        count = seen.get(header, 0) + 1
        seen[header] = count

        if count > 1:
            header = f"{header}_{count}"

        headers.append(header)

    return headers


def row_to_dict(headers: list[str], values: tuple[Any, ...]) -> dict[str, Any]:
    data: dict[str, Any] = {}

    for index, value in enumerate(values):
        if index < len(headers):
            key = headers[index]
        else:
            key = f"column_{index + 1}"

        if is_fallback_column(key) and not cell_has_value(value):
            continue

        data[key] = clean_cell_value(value)

    return data


def normalize_data(
    data: dict[str, Any],
    alias_lookup: dict[str, str],
) -> dict[str, Any]:
    normalized: dict[str, Any] = {}

    for key, value in data.items():
        canonical_key = alias_lookup.get(key)

        if canonical_key and cell_has_value(value):
            if is_url_field(canonical_key) and not is_url_like(value):
                continue

            normalized[canonical_key] = value

    return normalized


def build_alias_lookup(config: ExcelParserConfig) -> dict[str, str]:
    alias_lookup: dict[str, str] = {}

    for canonical_key, aliases in config.column_aliases.items():
        alias_lookup[normalize_key(canonical_key)] = canonical_key

        for alias in aliases:
            alias_lookup[normalize_key(alias)] = canonical_key

    return alias_lookup


def row_has_value(values: tuple[Any, ...]) -> bool:
    return any(cell_has_value(value) for value in values)


def row_empty_ratio(values: tuple[Any, ...]) -> float:
    if not values:
        return 1.0

    empty_cells = sum(1 for value in values if not cell_has_value(value))
    return empty_cells / len(values)


def row_exceeds_empty_ratio(
    values: tuple[Any, ...],
    max_empty_ratio: float | None,
) -> bool:
    if max_empty_ratio is None:
        return False

    return row_empty_ratio(values) >= max_empty_ratio


def cell_has_value(value: Any) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    return True


def clean_cell_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()

    return value


def is_fallback_column(key: str) -> bool:
    if not key.startswith("column_"):
        return False

    return key.removeprefix("column_").isdigit()


def is_url_field(key: str) -> bool:
    return key.endswith("_url")


def is_url_like(value: Any) -> bool:
    if not isinstance(value, str):
        return False

    cleaned_value = value.strip()

    if not cleaned_value or any(character.isspace() for character in cleaned_value):
        return False

    parsed_value = urlparse(cleaned_value)

    if parsed_value.scheme in {"http", "https"} and parsed_value.netloc:
        return True

    if cleaned_value.startswith("www."):
        return True

    return "." in cleaned_value and not cleaned_value.startswith(".")


def normalize_key(value: Any) -> str:
    key = str(value).strip().lower()
    key = key.replace("-", " ").replace("_", " ")
    key = " ".join(key.split())
    return key.replace(" ", "_")
