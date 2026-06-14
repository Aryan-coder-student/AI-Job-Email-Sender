from __future__ import annotations

from app.core.exceptions.base import AppError


class MatchingError(AppError):
    """Base error for hybrid matching operations."""
