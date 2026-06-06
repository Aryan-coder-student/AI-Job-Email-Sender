from __future__ import annotations

import pytest

from app.core.exceptions import InvalidExcelError
from app.modules.excel.config import ExcelParserConfig
from app.modules.excel.utils import (
    build_alias_lookup,
    build_headers,
    cell_has_value,
    clean_cell_value,
    is_fallback_column,
    is_url_field,
    is_url_like,
    normalize_data,
    normalize_key,
    row_empty_ratio,
    row_exceeds_empty_ratio,
    row_has_value,
    row_to_dict,
    select_sheets,
)


class DummySheet:
    def __init__(self, title: str) -> None:
        self.title = title


def test_select_sheets_uses_named_sheets_first() -> None:
    sheet_one = DummySheet("One")
    sheet_two = DummySheet("Two")

    selected = select_sheets(
        [sheet_one, sheet_two],
        ExcelParserConfig(sheet_count=1, sheet_names=("Two",)),
    )

    assert selected == [sheet_two]


def test_select_sheets_rejects_missing_named_sheet() -> None:
    with pytest.raises(InvalidExcelError, match="Missing sheets: Missing"):
        select_sheets([DummySheet("One")], ExcelParserConfig(sheet_names=("Missing",)))


def test_select_sheets_uses_sheet_count() -> None:
    sheets = [DummySheet("One"), DummySheet("Two"), DummySheet("Three")]

    assert select_sheets(sheets, ExcelParserConfig(sheet_count=2)) == sheets[:2]
    assert select_sheets(sheets, ExcelParserConfig(sheet_count=None)) == sheets


def test_build_headers_normalizes_blanks_and_duplicates() -> None:
    headers = build_headers(("Company Name", "Company Name", None, "Job-URL", ""))

    assert headers == [
        "company_name",
        "company_name_2",
        "column_3",
        "job_url",
        "column_5",
    ]


def test_row_to_dict_trims_strings_and_keeps_extra_columns() -> None:
    data = row_to_dict(
        ["company", "email", "column_3", "column_4"],
        (" Acme ", " hr@acme.com ", "extra", None),
    )

    assert data == {
        "company": "Acme",
        "email": "hr@acme.com",
        "column_3": "extra",
    }


def test_row_to_dict_keeps_empty_named_columns() -> None:
    data = row_to_dict(["company", "notes"], ("Acme", None))

    assert data == {
        "company": "Acme",
        "notes": None,
    }


def test_normalize_data_keeps_known_non_empty_fields() -> None:
    alias_lookup = build_alias_lookup(ExcelParserConfig())

    normalized = normalize_data(
        {
            "company": "Acme",
            "website": "https://acme.test",
            "linkedin": "https://linkedin.com/company/acme",
            "apply_link": "https://acme.test/jobs/1",
            "mail": "hr@acme.test",
            "unknown": "ignored",
            "contact_name": "   ",
        },
        alias_lookup,
    )

    assert normalized == {
        "company_name": "Acme",
        "company_url": "https://acme.test",
        "company_linkedin_url": "https://linkedin.com/company/acme",
        "job_url": "https://acme.test/jobs/1",
        "hr_email": "hr@acme.test",
    }


def test_normalize_data_supports_remotive_headers() -> None:
    alias_lookup = build_alias_lookup(ExcelParserConfig())

    normalized = normalize_data(
        {
            "company_name": "Zemanta",
            "what_do_they_do_(verbatim_10_words_max.)": (
                "Content Ads, Amplified & Optimized"
            ),
            "link_to_website": "http://www.zemanta.com/",
            "link_to_jobpage": "https://zemanta.workable.com/",
        },
        alias_lookup,
    )

    assert normalized == {
        "company_name": "Zemanta",
        "company_description": "Content Ads, Amplified & Optimized",
        "company_url": "http://www.zemanta.com/",
        "job_url": "https://zemanta.workable.com/",
    }


def test_normalize_data_skips_invalid_url_field_values() -> None:
    alias_lookup = build_alias_lookup(ExcelParserConfig())

    normalized = normalize_data(
        {
            "company_name": "Remotive Promo",
            "link_to_website": "💼 🏠🤗💻",
            "link_to_jobpage": "angel list",
        },
        alias_lookup,
    )

    assert normalized == {"company_name": "Remotive Promo"}


def test_build_alias_lookup_contains_canonical_and_alias_keys() -> None:
    alias_lookup = build_alias_lookup(ExcelParserConfig())

    assert alias_lookup["company_url"] == "company_url"
    assert alias_lookup["website"] == "company_url"
    assert alias_lookup["link_to_website"] == "company_url"
    assert alias_lookup["linkedin"] == "company_linkedin_url"
    assert alias_lookup["job_link"] == "job_url"
    assert alias_lookup["link_to_jobpage"] == "job_url"


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, False), ("", False), ("   ", False), ("Acme", True), (0, True)],
)
def test_cell_has_value(value: object, expected: bool) -> None:
    assert cell_has_value(value) is expected


def test_row_has_value() -> None:
    assert row_has_value((None, " ", "")) is False
    assert row_has_value((None, " Acme ", "")) is True


def test_row_empty_ratio() -> None:
    assert row_empty_ratio(()) == 1.0
    assert row_empty_ratio((None, "", " ", "Acme")) == 0.75


def test_row_exceeds_empty_ratio() -> None:
    values = (None, "", " ", "Acme")

    assert row_exceeds_empty_ratio(values, None) is False
    assert row_exceeds_empty_ratio(values, 0.75) is True
    assert row_exceeds_empty_ratio(values, 0.8) is False


def test_clean_cell_value() -> None:
    assert clean_cell_value(" Acme ") == "Acme"
    assert clean_cell_value(42) == 42


def test_is_fallback_column() -> None:
    assert is_fallback_column("column_16") is True
    assert is_fallback_column("column_name") is False
    assert is_fallback_column("company_column_1") is False


def test_is_url_field() -> None:
    assert is_url_field("company_url") is True
    assert is_url_field("job_url") is True
    assert is_url_field("company_name") is False


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://example.com", True),
        ("http://example.com/jobs", True),
        ("www.example.com", True),
        ("example.com/jobs", True),
        ("angel list", False),
        ("💼 🏠🤗💻", False),
        ("", False),
        (None, False),
    ],
)
def test_is_url_like(value: object, expected: bool) -> None:
    assert is_url_like(value) is expected


def test_normalize_key() -> None:
    assert normalize_key(" Company-LinkedIn URL ") == "company_linkedin_url"
