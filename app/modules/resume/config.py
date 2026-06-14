from __future__ import annotations

from dataclasses import dataclass, field

from app.core.constants import RESUME_ALLOWED_EXTENSIONS, RESUME_SECTION_ALIASES
from app.modules.resume.validator import validate_resume_parser_config


@dataclass(frozen=True)
class ResumeParserConfig:
    allowed_extensions: tuple[str, ...] = RESUME_ALLOWED_EXTENSIONS
    section_aliases: dict[str, tuple[str, ...]] = field(default_factory=lambda: RESUME_SECTION_ALIASES)
    max_file_size_bytes: int = 5 * 1024 * 1024
    max_cleaned_text_chars: int = 200000
    llm_max_tokens: int = 3000

    def validate(self) -> None:
        validate_resume_parser_config(self)
