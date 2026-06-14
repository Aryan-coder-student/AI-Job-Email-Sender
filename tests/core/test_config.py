from __future__ import annotations

from app.core.config import DEFAULT_LOG_LEVEL, LoggingConfig


def test_logging_config_defaults() -> None:
    config = LoggingConfig()

    assert config.level == DEFAULT_LOG_LEVEL
    assert config.log_file is None
