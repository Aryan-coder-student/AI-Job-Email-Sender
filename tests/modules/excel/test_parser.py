from __future__ import annotations

import builtins
from io import BytesIO

import pytest

from app.core.exceptions import InvalidExcelError
from app.modules.excel.config import ExcelParserConfig
from app.modules.excel.parser import (
    ParsedExcelRow,
    ParsedExcelSheet,
    ParsedExcelWorkbook,
    parse_excel_from_upload,
)


def test_parsed_excel_dataclasses_to_dict_and_company_records() -> None:
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
    workbook = ParsedExcelWorkbook(filename="companies.xlsx", sheets=[sheet])

    assert row.to_dict() == {
        "sheet_name": "Companies",
        "row_number": 2,
        "data": {"company": "Acme"},
        "normalized": {"company_name": "Acme"},
    }
    assert sheet.parsed_rows == 1
    assert workbook.sheet_count == 1
    assert workbook.total_rows == 1
    assert workbook.total_populated_rows == 1
    assert workbook.rows == [row]
    assert workbook.to_company_records() == [
        {
            "company_name": "Acme",
            "source_sheet": "Companies",
            "source_row": 2,
            "raw_data": {"company": "Acme"},
        }
    ]
    assert workbook.to_dict()["sheets"][0]["rows"][0]["normalized"] == {
        "company_name": "Acme"
    }


def test_parse_excel_from_upload_rejects_invalid_filename_before_opening_workbook() -> None:
    with pytest.raises(InvalidExcelError, match="Unsupported Excel file type"):
        parse_excel_from_upload(b"not an excel file", filename="companies.csv")


def test_parse_excel_from_upload_wraps_missing_openpyxl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "openpyxl":
            raise ModuleNotFoundError("No module named 'openpyxl'")

        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(InvalidExcelError, match="openpyxl is required"):
        parse_excel_from_upload(b"not an excel file", filename="companies.xlsx")


def test_parse_excel_from_upload_wraps_invalid_workbook() -> None:
    with pytest.raises(InvalidExcelError, match="Could not open Excel file"):
        parse_excel_from_upload(b"not an excel file", filename="companies.xlsx")


def test_parse_excel_from_upload_reads_rows_and_normalizes_fields() -> None:
    openpyxl = pytest.importorskip("openpyxl")
    file_content = _make_excel_bytes(
        openpyxl,
        rows=[
            (
                "Company Name",
                "Website",
                "LinkedIn",
                "Job URL",
                "Description",
                "HR Email",
            ),
            (
                "Acme",
                "https://acme.test",
                "https://linkedin.com/company/acme",
                "https://acme.test/jobs/1",
                "Builds tools",
                "hr@acme.test",
            ),
            (None, None, None, None, None, None),
            (
                "Beta",
                "https://beta.test",
                None,
                "https://beta.test/jobs/2",
                "Builds APIs",
                "jobs@beta.test",
            ),
        ],
    )

    workbook = parse_excel_from_upload(
        file_content,
        filename="companies.xlsx",
        config=ExcelParserConfig(max_rows=1),
    )

    assert workbook.filename == "companies.xlsx"
    assert workbook.sheet_count == 1
    assert workbook.total_rows == 1
    assert workbook.total_populated_rows == 2

    sheet = workbook.sheets[0]
    assert sheet.name == "Companies"
    assert sheet.headers == [
        "company_name",
        "website",
        "linkedin",
        "job_url",
        "description",
        "hr_email",
    ]

    record = workbook.to_company_records()[0]
    assert record["company_name"] == "Acme"
    assert record["company_url"] == "https://acme.test"
    assert record["company_linkedin_url"] == "https://linkedin.com/company/acme"
    assert record["job_url"] == "https://acme.test/jobs/1"
    assert record["company_description"] == "Builds tools"
    assert record["hr_email"] == "hr@acme.test"
    assert record["source_row"] == 2


def test_parse_excel_from_upload_skips_rows_at_max_empty_ratio() -> None:
    openpyxl = pytest.importorskip("openpyxl")
    file_content = _make_excel_bytes(
        openpyxl,
        rows=[
            (
                "Company Name",
                "Website",
                "LinkedIn",
                "Job URL",
                "Description",
                "HR Email",
                "Contact Name",
                "Role",
                "Location",
                "Notes",
            ),
            ("Sparse", None, None, None, None, None, None, None, None, None),
            ("Acme", "https://acme.test", None, None, None, None, None, None, None, None),
        ],
    )

    workbook = parse_excel_from_upload(file_content, filename="companies.xlsx")

    assert workbook.total_populated_rows == 2
    assert workbook.total_rows == 1
    assert workbook.to_company_records()[0]["company_name"] == "Acme"
    assert workbook.to_company_records()[0]["source_row"] == 3


def test_parse_excel_from_upload_can_disable_sparse_row_filter() -> None:
    openpyxl = pytest.importorskip("openpyxl")
    file_content = _make_excel_bytes(
        openpyxl,
        rows=[
            ("Company Name", "Website", "LinkedIn", "Job URL", "Description"),
            ("Sparse", None, None, None, None),
        ],
    )

    workbook = parse_excel_from_upload(
        file_content,
        filename="companies.xlsx",
        config=ExcelParserConfig(max_empty_ratio=None),
    )

    assert workbook.total_rows == 1
    assert workbook.to_company_records()[0]["company_name"] == "Sparse"


def test_parse_excel_from_upload_supports_named_sheets() -> None:
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    first = workbook.active
    first.title = "Ignore"
    first.append(("Company Name",))
    first.append(("Wrong",))
    second = workbook.create_sheet("Companies")
    second.append(("Company Name",))
    second.append(("Acme",))

    stream = BytesIO()
    workbook.save(stream)

    parsed = parse_excel_from_upload(
        stream.getvalue(),
        filename="companies.xlsx",
        config=ExcelParserConfig(sheet_names=("Companies",)),
    )

    assert parsed.sheets[0].name == "Companies"
    assert parsed.to_company_records()[0]["company_name"] == "Acme"


def test_parse_excel_from_upload_rejects_empty_header_row() -> None:
    openpyxl = pytest.importorskip("openpyxl")
    file_content = _make_excel_bytes(
        openpyxl,
        rows=[
            (None, None),
            ("Acme", "https://acme.test"),
        ],
    )

    with pytest.raises(InvalidExcelError, match="does not contain headers"):
        parse_excel_from_upload(file_content, filename="companies.xlsx")


def _make_excel_bytes(openpyxl: object, rows: list[tuple[object, ...]]) -> bytes:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Companies"

    for row in rows:
        sheet.append(row)

    stream = BytesIO()
    workbook.save(stream)
    return stream.getvalue()
