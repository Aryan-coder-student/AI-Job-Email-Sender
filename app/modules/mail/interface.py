from __future__ import annotations

from typing import Protocol

from app.modules.mail.model import MailMessage, SendMailResult


class MailProvider(Protocol):
    name: str

    def send(self, message: MailMessage) -> SendMailResult:
        """Send an email message."""
