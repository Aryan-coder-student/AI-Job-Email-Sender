from __future__ import annotations

from app.core.exceptions.base import AppError


class MailError(AppError):
    """Base error for mail configuration and delivery failures."""


class MailConfigurationError(MailError):
    """Raised when SMTP/mail configuration is missing or invalid."""


class MailSendError(MailError):
    """Raised when an email cannot be sent."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
