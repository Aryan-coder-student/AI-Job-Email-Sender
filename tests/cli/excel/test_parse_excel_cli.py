from __future__ import annotations

import argparse
import json

import pytest

from app.core.exceptions import InvalidExcelError
from app.modules.excel.config import ExcelParserConfig
from app.modules.excel.parser import ParsedExcelRow, ParsedExcelSheet, ParsedExcelWorkbook
from cli.excel import parse_excel


def test_build_config_from_args() -> None:
    args = argparse.Namespace(
        all_sheets=True,
        sheet_count=1,
        max_rows=10,
        max_empty_ratio=0.75,
        keep_sparse_rows=False,
        header_row=2,
        sheet_name=["Companies", "More Companies"],
        download_timeout=5,
        max_download_mb=2.5,
    )

    config = parse_excel.build_config(args)

    assert config.sheet_count is None
    assert config.max_rows == 10
    assert config.max_empty_ratio == 0.75
    assert config.header_row == 2
    assert config.sheet_names == ("Companies", "More Companies")
    assert config.download_timeout_seconds == 5
    assert config.max_download_bytes == int(2.5 * 1024 * 1024)


def test_build_config_can_disable_sparse_row_filter() -> None:
    args = argparse.Namespace(
        all_sheets=False,
        sheet_count=1,
        max_rows=None,
        max_empty_ratio=0.9,
        keep_sparse_rows=True,
        header_row=1,
        sheet_name=[],
        download_timeout=20,
        max_download_mb=10,
    )

    config = parse_excel.build_config(args)

    assert config.max_empty_ratio is None


@pytest.mark.parametrize(
    ("source", "source_type", "expected"),
    [
        ("https://example.com/companies.xlsx", "auto", "url"),
        ("http://example.com/companies.xlsx", "auto", "url"),
        ("companies.xlsx", "auto", "path"),
        ("companies.xlsx", "path", "path"),
        ("companies.xlsx", "url", "url"),
    ],
)
def test_resolve_source_type(source: str, source_type: str, expected: str) -> None:
    assert parse_excel.resolve_source_type(source, source_type) == expected


def test_parse_source_uses_url_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    config = ExcelParserConfig()
    expected = make_workbook()

    monkeypatch.setattr(
        parse_excel,
        "parse_excel_from_url",
        lambda source, config: expected,
    )

    assert parse_excel.parse_source("https://example.com/file.xlsx", "auto", config) is expected


def test_parse_source_uses_path_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    config = ExcelParserConfig()
    expected = make_workbook()

    monkeypatch.setattr(
        parse_excel,
        "parse_excel_from_path",
        lambda source, config: expected,
    )

    assert parse_excel.parse_source("file.xlsx", "auto", config) is expected


def test_workbook_to_payload_records() -> None:
    payload = parse_excel.workbook_to_payload(make_workbook(), "records")

    assert payload == [
        {
            "company_name": "Acme",
            "source_sheet": "Companies",
            "source_row": 2,
            "raw_data": {"company": "Acme"},
        }
    ]


def test_workbook_to_payload_workbook() -> None:
    payload = parse_excel.workbook_to_payload(make_workbook(), "workbook")

    assert payload["filename"] == "companies.xlsx"
    assert payload["sheet_count"] == 1


def test_write_json_output_prints_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    parse_excel.write_json_output([{"company_name": "💼 Acme"}], None, compact=True)

    assert capsys.readouterr().out == '[{"company_name": "💼 Acme"}]\n'


def test_write_json_output_writes_file(tmp_path) -> None:
    output_file = tmp_path / "parsed.json"

    parse_excel.write_json_output([{"company_name": "Acme"}], output_file, compact=False)

    assert json.loads(output_file.read_text(encoding="utf-8")) == [
        {"company_name": "Acme"}
    ]


def test_positive_int() -> None:
    assert parse_excel.positive_int("3") == 3

    with pytest.raises(argparse.ArgumentTypeError):
        parse_excel.positive_int("0")


def test_positive_float() -> None:
    assert parse_excel.positive_float("2.5") == 2.5

    with pytest.raises(argparse.ArgumentTypeError):
        parse_excel.positive_float("0")


def test_ratio() -> None:
    assert parse_excel.ratio("0.75") == 0.75

    with pytest.raises(argparse.ArgumentTypeError):
        parse_excel.ratio("1.5")


def test_main_prints_records(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        parse_excel,
        "parse_source",
        lambda source, source_type, config: make_workbook(),
    )

    exit_code = parse_excel.main(["companies.xlsx", "--compact"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == [
        {
            "company_name": "Acme",
            "source_sheet": "Companies",
            "source_row": 2,
            "raw_data": {"company": "Acme"},
        }
    ]


def test_main_returns_error_for_parser_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_parse_source(
        source: str,
        source_type: str,
        config: ExcelParserConfig,
    ) -> ParsedExcelWorkbook:
        raise InvalidExcelError("bad excel")

    monkeypatch.setattr(parse_excel, "parse_source", fake_parse_source)

    exit_code = parse_excel.main(["companies.xlsx"])

    assert exit_code == 1
    assert "Error: bad excel" in capsys.readouterr().err


def make_workbook() -> ParsedExcelWorkbook:
    row = ParsedExcelRow(
        sheet_name="Companies",
        row_number=2,
        data={"company": "Acme"},
        normalized={"company_name": "Acme"},
    )
    sheet = ParsedExcelSheet(
        name="Companies",
        headers=["company"],
        rows=[row],
        total_populated_rows=1,
    )
    return ParsedExcelWorkbook(filename="companies.xlsx", sheets=[sheet])
