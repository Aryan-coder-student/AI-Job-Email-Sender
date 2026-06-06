from __future__ import annotations

import pytest

from app.core.exceptions import InvalidExcelError
from app.modules.excel.config import ExcelParserConfig
from app.modules.excel.validator import (
    validate_excel_filename,
    validate_excel_parser_config,
    validate_excel_url,
)


def test_excel_parser_config_defaults() -> None:
    config = ExcelParserConfig()

    assert config.sheet_count == 1
    assert config.max_rows is None
    assert config.max_empty_ratio == 0.9
    assert config.header_row == 1
    assert config.download_timeout_seconds == 20
    assert config.max_download_bytes == 10 * 1024 * 1024
    assert "company_url" in config.column_aliases
    assert "company_linkedin_url" in config.column_aliases
    assert "job_url" in config.column_aliases


def test_default_column_aliases_do_not_overlap() -> None:
    config = ExcelParserConfig()
    aliases_by_normalized_name: dict[str, str] = {}

    for canonical_key, aliases in config.column_aliases.items():
        names = (canonical_key, *aliases)

        for name in names:
            normalized_name = name.strip().lower().replace("-", " ").replace("_", " ")
            normalized_name = "_".join(normalized_name.split())
            previous_owner = aliases_by_normalized_name.get(normalized_name)

            assert previous_owner in (None, canonical_key), (
                f"{name!r} is mapped by both {previous_owner!r} and {canonical_key!r}"
            )

            aliases_by_normalized_name[normalized_name] = canonical_key


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    [
        ("sheet_count", 0, "sheet_count must be at least 1"),
        ("max_rows", 0, "max_rows must be at least 1"),
        ("max_empty_ratio", 0, "max_empty_ratio must be greater than 0"),
        ("max_empty_ratio", 1.1, "max_empty_ratio must be greater than 0"),
        ("header_row", 0, "header_row must be at least 1"),
        ("download_timeout_seconds", 0, "download_timeout_seconds must be at least 1"),
        ("max_download_bytes", 0, "max_download_bytes must be at least 1"),
    ],
)
def test_validate_excel_parser_config_rejects_invalid_values(
    field_name: str,
    value: int,
    message: str,
) -> None:
    config = ExcelParserConfig(**{field_name: value})

    with pytest.raises(ValueError, match=message):
        validate_excel_parser_config(config)


def test_excel_parser_config_validate_delegates_to_validator() -> None:
    ExcelParserConfig(sheet_count=None, max_rows=None).validate()

    with pytest.raises(ValueError, match="sheet_count must be at least 1"):
        ExcelParserConfig(sheet_count=0).validate()


@pytest.mark.parametrize(
    "filename",
    [
        None,
        "",
        "companies.xlsx",
        "companies.XLSM",
        "template.xltx",
        "template.XLTM",
    ],
)
def test_validate_excel_filename_accepts_supported_names(filename: str | None) -> None:
    validate_excel_filename(filename)


def test_validate_excel_filename_rejects_unsupported_extension() -> None:
    with pytest.raises(InvalidExcelError, match="Unsupported Excel file type"):
        validate_excel_filename("companies.csv")


@pytest.mark.parametrize("url", ["https://example.com/file.xlsx", "http://example.com"])
def test_validate_excel_url_accepts_http_urls(url: str) -> None:
    validate_excel_url(url)


@pytest.mark.parametrize("url", ["ftp://example.com/file.xlsx", "/tmp/file.xlsx", ""])
def test_validate_excel_url_rejects_non_http_urls(url: str) -> None:
    with pytest.raises(InvalidExcelError, match="Excel URL must start"):
        validate_excel_url(url)
