from __future__ import annotations

from app.core.exceptions.base import AppError


class VectorError(AppError):
    """Base error for vector store operations."""


class VectorConfigurationError(VectorError):
    """Raised when vector/Qdrant configuration is missing or invalid."""
