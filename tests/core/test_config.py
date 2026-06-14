from __future__ import annotations

from app.core.config import DEFAULT_LOG_LEVEL, LoggingConfig
from app.core.settings import reset_settings


def test_logging_config_defaults() -> None:
    config = LoggingConfig()

    assert config.level == DEFAULT_LOG_LEVEL
    assert config.log_file is None


def test_logging_config_from_env_uses_defaults(monkeypatch) -> None:
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("LOG_FILE", raising=False)
    reset_settings()

    config = LoggingConfig.from_env()

    assert config.level == DEFAULT_LOG_LEVEL
    assert config.log_file is None


def test_logging_config_from_env_normalizes_blank_values(monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "  debug  ")
    monkeypatch.setenv("LOG_FILE", "  logs/app.log  ")
    reset_settings()

    config = LoggingConfig.from_env()

    assert config.level == "debug"
    assert config.log_file == "logs/app.log"


def test_logging_config_from_env_falls_back_for_blank_level(monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "   ")
    monkeypatch.delenv("LOG_FILE", raising=False)
    reset_settings()

    config = LoggingConfig.from_env()

    assert config.level == DEFAULT_LOG_LEVEL
    assert config.log_file is None
