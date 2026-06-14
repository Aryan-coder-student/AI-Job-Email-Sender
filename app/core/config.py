from __future__ import annotations

from dataclasses import dataclass

from app.core.settings import get_settings
from app.core.string_normalizers import string_or_none

DEFAULT_LOG_LEVEL = "INFO"


@dataclass(frozen=True)
class LoggingConfig:
    level: str = DEFAULT_LOG_LEVEL
    log_file: str | None = None

    @classmethod
    def from_env(cls) -> LoggingConfig:
        settings = get_settings()
        level = string_or_none(settings.log_level) or DEFAULT_LOG_LEVEL
        log_file = string_or_none(settings.log_file)
        return cls(level=level, log_file=log_file)
