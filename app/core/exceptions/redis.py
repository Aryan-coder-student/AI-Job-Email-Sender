from __future__ import annotations

from app.core.exceptions.base import AppError


class RedisError(AppError):
    """Base error for Redis operations."""


class RedisConfigurationError(RedisError):
    """Raised when Redis configuration is missing or invalid."""


class RedisOperationError(RedisError):
    """Raised when a Redis command fails."""
