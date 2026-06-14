from __future__ import annotations

import logging
import sys
from pathlib import Path

from app.core.config import DEFAULT_LOG_LEVEL, LoggingConfig

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)


def configure_logging(
    *,
    level: str | None = None,
    log_file: str | Path | None = None,
) -> None:
    global _configured

    if _configured:
        return

    env_config = LoggingConfig.from_env()
    resolved_level = _resolve_log_level(level or env_config.level)
    resolved_log_file = log_file if log_file is not None else env_config.log_file

    root_logger = logging.getLogger()
    root_logger.setLevel(resolved_level)

    if root_logger.handlers:
        _configured = True
        return

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    root_logger.addHandler(_build_stream_handler(formatter))

    if resolved_log_file:
        root_logger.addHandler(_build_file_handler(str(resolved_log_file), formatter))

    _configured = True


def _resolve_log_level(level_name: str) -> int:
    normalized_level = level_name.strip().upper()

    if normalized_level not in logging.getLevelNamesMapping():
        return logging.getLevelNamesMapping()[DEFAULT_LOG_LEVEL]

    return logging.getLevelNamesMapping()[normalized_level]


def _build_stream_handler(formatter: logging.Formatter) -> logging.Handler:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    return handler


def _build_file_handler(log_file: str, formatter: logging.Formatter) -> logging.Handler:
    file_path = Path(log_file)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(file_path, encoding="utf-8")
    handler.setFormatter(formatter)
    return handler
