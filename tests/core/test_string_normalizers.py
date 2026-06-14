from __future__ import annotations

from app.core.string_normalizers import string_list, string_or_empty, string_or_none


def test_string_list_filters_non_strings_and_blanks() -> None:
    assert string_list([" a ", "", 1, "b"]) == ["a", "b"]
    assert string_list("not-a-list") == []


def test_string_or_none() -> None:
    assert string_or_none("  value  ") == "value"
    assert string_or_none("   ") is None
    assert string_or_none(None) is None


def test_string_or_empty() -> None:
    assert string_or_empty("  value  ") == "value"
    assert string_or_empty(123) == ""
