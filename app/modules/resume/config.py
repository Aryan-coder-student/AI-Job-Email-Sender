from __future__ import annotations

from dataclasses import dataclass

from app.modules.resume.validator import validate_resume_parser_config
from setting import RESUME_ALLOWED_EXTENSIONS


@dataclass(frozen=True)
class ResumeParserConfig:
    allowed_extensions: tuple[str, ...] = RESUME_ALLOWED_EXTENSIONS
    max_file_size_bytes: int = 5 * 1024 * 1024
    max_cleaned_text_chars: int = 200000
    llm_max_tokens: int = 1800

    def validate(self) -> None:
        validate_resume_parser_config(self)
