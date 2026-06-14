from __future__ import annotations

import pytest

from app.core.exceptions import MailConfigurationError, MailSendError
from app.modules.mail.config import MailConfig
from app.modules.mail.model import MailAttachment, MailMessage
from app.modules.mail.validator import validate_email_address, validate_mail_message


def test_mail_config_from_env_uses_gmail_preset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAIL_PROVIDER", "gmail")
    monkeypatch.setenv("SMTP_USERNAME", "user@gmail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "app-password")

    config = MailConfig.from_env()

    assert config.provider == "gmail"
    assert config.host == "smtp.gmail.com"
    assert config.port == 587
    assert config.use_tls is True
    assert config.from_email == "user@gmail.com"


def test_mail_config_from_env_requires_custom_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAIL_PROVIDER", "custom")
    monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")

    with pytest.raises(MailConfigurationError, match="SMTP_HOST is required"):
        MailConfig.from_env()


def test_mail_config_rejects_tls_and_ssl_together(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAIL_PROVIDER", "custom")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setenv("SMTP_USE_TLS", "true")
    monkeypatch.setenv("SMTP_USE_SSL", "true")

    with pytest.raises(MailConfigurationError, match="cannot both be enabled"):
        MailConfig.from_env()


def test_validate_email_address_rejects_invalid_value() -> None:
    with pytest.raises(MailConfigurationError, match="Invalid to email"):
        validate_email_address("not-an-email", field_name="to")


def test_validate_mail_message_requires_recipients() -> None:
    with pytest.raises(MailSendError, match="At least one recipient"):
        validate_mail_message(
            MailMessage(
                to=[],
                subject="Hello",
                body_text="Body",
            )
        )


def test_validate_mail_message_requires_attachment_filename() -> None:
    with pytest.raises(MailSendError, match="Attachment filename"):
        validate_mail_message(
            MailMessage(
                to=["hr@acme.com"],
                subject="Hello",
                body_text="Body",
                attachments=[MailAttachment(filename="  ", content=b"pdf")],
            )
        )
