from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.exceptions import InvalidResumeError


def validate_resume_parser_config(config: Any) -> None:
    if not config.allowed_extensions:
        raise ValueError("allowed_extensions must contain at least one extension.")

    for extension in config.allowed_extensions:
        if not extension.startswith("."):
            raise ValueError("allowed_extensions values must start with '.'.")

    if config.max_file_size_bytes < 1:
        raise ValueError("max_file_size_bytes must be at least 1.")

    if config.max_cleaned_text_chars < 1:
        raise ValueError("max_cleaned_text_chars must be at least 1.")

    if config.llm_max_tokens < 1:
        raise ValueError("llm_max_tokens must be at least 1.")


def validate_resume_filename(
    filename: str | None,
    allowed_extensions: tuple[str, ...],
) -> str:
    if not filename:
        raise InvalidResumeError("Resume filename is required.")

    extension = Path(filename).suffix.lower()

    if not extension:
        raise InvalidResumeError("Resume file must have an extension.")

    if extension not in allowed_extensions:
        supported = ", ".join(allowed_extensions)
        raise InvalidResumeError(f"Unsupported resume file type. Use one of: {supported}.")

    return extension


def validate_resume_content(
    file_content: bytes,
    max_file_size_bytes: int,
) -> None:
    if not file_content:
        raise InvalidResumeError("Resume file is empty.")

    if len(file_content) > max_file_size_bytes:
        raise InvalidResumeError("Resume file is larger than the configured size limit.")


def validate_resume_text(raw_text: str) -> None:
    if not raw_text.strip():
        raise InvalidResumeError("Resume parser did not extract any text.")
