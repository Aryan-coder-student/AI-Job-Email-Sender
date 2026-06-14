from __future__ import annotations

from dataclasses import dataclass

from setting import LOG_FILE_ENV, LOG_LEVEL_ENV, get_env

DEFAULT_LOG_LEVEL = "INFO"


@dataclass(frozen=True)
class LoggingConfig:
    level: str = DEFAULT_LOG_LEVEL
    log_file: str | None = None

    @classmethod
    def from_env(cls) -> LoggingConfig:
        level = get_env(LOG_LEVEL_ENV, DEFAULT_LOG_LEVEL)
        log_file = get_env(LOG_FILE_ENV)

        normalized_level = level.strip() if isinstance(level, str) and level.strip() else DEFAULT_LOG_LEVEL
        normalized_log_file = log_file.strip() if isinstance(log_file, str) and log_file.strip() else None

        return cls(level=normalized_level, log_file=normalized_log_file)
