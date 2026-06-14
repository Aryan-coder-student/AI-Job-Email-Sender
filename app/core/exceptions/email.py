from __future__ import annotations

from app.core.exceptions.base import AppError


class EmailError(AppError):
    """Base error for email draft and queue operations."""


class EmailConfigurationError(EmailError):
    """Raised when email/Redis configuration is missing or invalid."""


class EmailDraftError(EmailError):
    """Raised when draft generation or parsing fails."""


class EmailQueueError(EmailError):
    """Raised when queue operations fail."""
