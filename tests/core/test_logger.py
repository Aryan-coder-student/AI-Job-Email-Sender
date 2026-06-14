from __future__ import annotations

import logging

import pytest

import app.core.logger as logger_module
from app.core.config import DEFAULT_LOG_LEVEL
from app.core.logger import configure_logging, get_logger


@pytest.fixture(autouse=True)
def reset_logging_state() -> None:
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    root_logger.setLevel(logging.WARNING)
    logger_module._configured = False
    yield
    logger_module._configured = False


def test_get_logger_returns_named_logger() -> None:
    logger = get_logger("app.modules.github.parser")

    assert logger.name == "app.modules.github.parser"


def test_configure_logging_is_idempotent() -> None:
    configure_logging(level="DEBUG")
    handler_count = len(logging.getLogger().handlers)

    configure_logging(level="ERROR")

    assert len(logging.getLogger().handlers) == handler_count


def test_configure_logging_uses_requested_level(caplog) -> None:
    configure_logging(level="INFO")
    logger = get_logger("app.test")

    with caplog.at_level(logging.INFO):
        logger.info("info message")

    assert "info message" in caplog.text
    assert "app.test" in caplog.text


def test_resolve_log_level_falls_back_to_info_for_invalid_value() -> None:
    assert logger_module._resolve_log_level("not-a-level") == logging.getLevelNamesMapping()[DEFAULT_LOG_LEVEL]
