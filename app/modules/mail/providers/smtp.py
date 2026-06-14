from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.exceptions import MailSendError
from app.core.logger import get_logger
from app.modules.mail.config import MailConfig
from app.modules.mail.model import MailMessage, SendMailResult

logger = get_logger(__name__)


class SmtpMailProvider:
    name = "smtp"

    def __init__(self, config: MailConfig) -> None:
        self.config = config
        self.name = config.provider

    def send(self, message: MailMessage) -> SendMailResult:
        email_message = _build_email_message(message, self.config.from_email)
        recipients = _collect_recipients(message)

        logger.info(
            "Sending email provider=%s host=%s recipients=%s subject=%s",
            self.name,
            self.config.host,
            len(recipients),
            message.subject,
        )

        try:
            refused = _send_via_smtp(self.config, email_message)
        except smtplib.SMTPException as error:
            logger.exception(
                "SMTP send failed provider=%s host=%s recipients=%s",
                self.name,
                self.config.host,
                len(recipients),
            )
            raise MailSendError(
                f"Failed to send email via SMTP: {error}",
                provider=self.name,
            ) from error
        except OSError as error:
            logger.exception(
                "SMTP connection failed provider=%s host=%s",
                self.name,
                self.config.host,
            )
            raise MailSendError(
                f"Failed to connect to SMTP server: {error}",
                provider=self.name,
            ) from error

        if refused:
            refused_summary = _format_refused_recipients(refused)
            raise MailSendError(
                f"SMTP server refused recipients: {refused_summary}",
                provider=self.name,
            )

        message_id = email_message.get("Message-ID")
        logger.info(
            "Email sent provider=%s recipients=%s message_id=%s",
            self.name,
            len(recipients),
            message_id,
        )

        return SendMailResult(
            provider=self.name,
            recipients=recipients,
            message_id=message_id,
            metadata={
                "host": self.config.host,
                "port": self.config.port,
                "from_email": self.config.from_email,
            },
        )


def _send_via_smtp(
    config: MailConfig,
    email_message: EmailMessage,
) -> dict[str, tuple[int, bytes]]:
    smtp_class = smtplib.SMTP_SSL if config.use_ssl else smtplib.SMTP

    with smtp_class(config.host, config.port, timeout=config.timeout_seconds) as client:
        if not config.use_ssl and config.use_tls:
            client.starttls()
        client.login(config.username, config.password)
        return client.send_message(email_message)


def _build_email_message(message: MailMessage, from_email: str) -> EmailMessage:
    email_message = EmailMessage()
    email_message["From"] = from_email
    email_message["To"] = ", ".join(message.to)
    email_message["Subject"] = message.subject

    if message.cc:
        email_message["Cc"] = ", ".join(message.cc)

    if message.reply_to:
        email_message["Reply-To"] = message.reply_to

    if message.body_html and message.body_text:
        email_message.set_content(message.body_text)
        email_message.add_alternative(message.body_html, subtype="html")
    elif message.body_html:
        email_message.set_content(message.body_html, subtype="html")
    else:
        email_message.set_content(message.body_text)

    for attachment in message.attachments:
        email_message.add_attachment(
            attachment.content,
            maintype=_maintype(attachment.content_type),
            subtype=_subtype(attachment.content_type),
            filename=attachment.filename,
        )

    return email_message


def _collect_recipients(message: MailMessage) -> list[str]:
    return list(dict.fromkeys([*message.to, *message.cc, *message.bcc]))


def _format_refused_recipients(refused: dict[str, tuple[int, bytes]]) -> str:
    return ", ".join(f"{recipient} ({code})" for recipient, (code, _) in refused.items())


def _maintype(content_type: str) -> str:
    return content_type.split("/", 1)[0]


def _subtype(content_type: str) -> str:
    if "/" not in content_type:
        return "octet-stream"
    return content_type.split("/", 1)[1]
