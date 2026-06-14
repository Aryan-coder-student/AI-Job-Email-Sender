from __future__ import annotations

import re
from typing import TYPE_CHECKING

from app.core.exceptions import MailConfigurationError, MailSendError
from app.modules.mail.model import MailMessage

if TYPE_CHECKING:
    from app.modules.mail.config import MailConfig

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_mail_config(config: MailConfig) -> None:
    if not config.host:
        raise MailConfigurationError("SMTP host is required.")

    if config.port < 1 or config.port > 65535:
        raise MailConfigurationError("SMTP port must be between 1 and 65535.")

    if not config.username:
        raise MailConfigurationError("SMTP username is required.")

    if not config.password:
        raise MailConfigurationError("SMTP password is required.")

    if not config.from_email:
        raise MailConfigurationError("SMTP from email is required.")

    validate_email_address(config.from_email, field_name="from email")
    validate_email_address(config.username, field_name="username")

    if config.use_tls and config.use_ssl:
        raise MailConfigurationError("SMTP_USE_TLS and SMTP_USE_SSL cannot both be enabled.")

    if config.timeout_seconds < 1:
        raise MailConfigurationError("SMTP timeout must be at least 1 second.")


def validate_mail_message(message: MailMessage) -> None:
    if not message.to:
        raise MailSendError("At least one recipient is required.")

    if not message.subject.strip():
        raise MailSendError("Email subject is required.")

    if not message.body_text.strip() and not message.body_html:
        raise MailSendError("Email body is required.")

    for field_name, addresses in (
        ("to", message.to),
        ("cc", message.cc),
        ("bcc", message.bcc),
    ):
        for address in addresses:
            validate_email_address(address, field_name=field_name)

    if message.reply_to:
        validate_email_address(message.reply_to, field_name="reply_to")

    for attachment in message.attachments:
        if not attachment.filename.strip():
            raise MailSendError("Attachment filename is required.")


def validate_email_address(address: str, *, field_name: str) -> str:
    normalized = address.strip()
    if not normalized or not EMAIL_PATTERN.fullmatch(normalized):
        raise MailConfigurationError(f"Invalid {field_name} email address: {address}")

    return normalized
