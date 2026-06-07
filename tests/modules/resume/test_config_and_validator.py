from __future__ import annotations

import pytest

from app.core.exceptions import InvalidResumeError
from app.modules.resume.config import ResumeParserConfig
from app.modules.resume.validator import (
    validate_resume_content,
    validate_resume_filename,
    validate_resume_parser_config,
    validate_resume_text,
)


def test_resume_parser_config_defaults() -> None:
    config = ResumeParserConfig()

    assert config.allowed_extensions == (".txt", ".pdf", ".docx")
    assert config.max_file_size_bytes == 5 * 1024 * 1024
    assert config.max_cleaned_text_chars == 20_000
    assert config.llm_max_tokens == 1800


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"allowed_extensions": ()}, "allowed_extensions must contain"),
        ({"allowed_extensions": ("txt",)}, "must start with"),
        ({"max_file_size_bytes": 0}, "max_file_size_bytes must be at least 1"),
        ({"max_cleaned_text_chars": 0}, "max_cleaned_text_chars must be at least 1"),
        ({"llm_max_tokens": 0}, "llm_max_tokens must be at least 1"),
    ],
)
def test_validate_resume_parser_config_rejects_invalid_values(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_resume_parser_config(ResumeParserConfig(**kwargs))


@pytest.mark.parametrize("filename", ["resume.txt", "resume.PDF", "resume.docx"])
def test_validate_resume_filename_accepts_supported_files(filename: str) -> None:
    extension = validate_resume_filename(filename, ResumeParserConfig().allowed_extensions)

    assert extension == f".{filename.rsplit('.', 1)[1].lower()}"


@pytest.mark.parametrize(
    ("filename", "message"),
    [
        (None, "filename is required"),
        ("resume", "must have an extension"),
        ("resume.csv", "Unsupported resume file type"),
    ],
)
def test_validate_resume_filename_rejects_invalid_files(
    filename: str | None,
    message: str,
) -> None:
    with pytest.raises(InvalidResumeError, match=message):
        validate_resume_filename(filename, ResumeParserConfig().allowed_extensions)


def test_validate_resume_content_accepts_non_empty_small_file() -> None:
    validate_resume_content(b"resume", max_file_size_bytes=10)


def test_validate_resume_content_rejects_empty_file() -> None:
    with pytest.raises(InvalidResumeError, match="empty"):
        validate_resume_content(b"", max_file_size_bytes=10)


def test_validate_resume_content_rejects_large_file() -> None:
    with pytest.raises(InvalidResumeError, match="larger"):
        validate_resume_content(b"resume", max_file_size_bytes=2)


def test_validate_resume_text() -> None:
    validate_resume_text("hello")

    with pytest.raises(InvalidResumeError, match="did not extract any text"):
        validate_resume_text(" ")
