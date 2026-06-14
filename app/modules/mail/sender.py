from __future__ import annotations

from app.core.logger import get_logger
from app.modules.mail.interface import MailProvider
from app.modules.mail.model import MailMessage, SendMailResult
from app.modules.mail.validator import validate_mail_message

logger = get_logger(__name__)


class MailSender:
    def __init__(self, provider: MailProvider) -> None:
        self.provider = provider

    def send(self, message: MailMessage) -> SendMailResult:
        validate_mail_message(message)
        logger.debug(
            "Validated email message provider=%s recipients=%s subject=%s",
            self.provider.name,
            len(message.to),
            message.subject,
        )
        return self.provider.send(message)
