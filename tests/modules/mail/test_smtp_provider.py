from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.exceptions import MailSendError
from app.modules.mail.config import MailConfig
from app.modules.mail.model import MailAttachment, MailMessage
from app.modules.mail.providers.smtp import SmtpMailProvider


def _mail_config(**overrides: object) -> MailConfig:
    defaults = {
        "provider": "gmail",
        "host": "smtp.gmail.com",
        "port": 587,
        "username": "user@gmail.com",
        "password": "app-password",
        "from_email": "user@gmail.com",
        "use_tls": True,
        "use_ssl": False,
        "timeout_seconds": 30,
    }
    defaults.update(overrides)
    return MailConfig(**defaults)


class FakeSmtpClient:
    def __init__(self) -> None:
        self.started_tls = False
        self.logged_in = False
        self.sent_message = None

    def __enter__(self) -> FakeSmtpClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def starttls(self) -> None:
        self.started_tls = True

    def login(self, username: str, password: str) -> None:
        self.logged_in = True
        assert username == "user@gmail.com"
        assert password == "app-password"

    def send_message(self, message) -> dict[str, tuple[int, bytes]]:
        self.sent_message = message
        return {}


@patch("app.modules.mail.providers.smtp.smtplib.SMTP")
def test_smtp_provider_sends_with_starttls(mock_smtp) -> None:
    client = FakeSmtpClient()
    mock_smtp.return_value = client
    provider = SmtpMailProvider(_mail_config())

    result = provider.send(
        MailMessage(
            to=["hr@acme.com"],
            subject="Application",
            body_text="Hello",
            attachments=[MailAttachment(filename="resume.pdf", content=b"pdf", content_type="application/pdf")],
        )
    )

    assert client.started_tls is True
    assert client.logged_in is True
    assert client.sent_message is not None
    assert result.provider == "gmail"
    assert result.recipients == ["hr@acme.com"]


@patch("app.modules.mail.providers.smtp.smtplib.SMTP_SSL")
def test_smtp_provider_uses_ssl_client(mock_smtp_ssl) -> None:
    client = FakeSmtpClient()
    mock_smtp_ssl.return_value = client
    provider = SmtpMailProvider(_mail_config(use_ssl=True, use_tls=False, port=465))

    provider.send(
        MailMessage(
            to=["hr@acme.com"],
            subject="Application",
            body_text="Hello",
        )
    )

    mock_smtp_ssl.assert_called_once()
    assert client.logged_in is True


@patch("app.modules.mail.providers.smtp.smtplib.SMTP")
def test_smtp_provider_raises_when_recipients_are_refused(mock_smtp) -> None:
    client = FakeSmtpClient()
    mock_smtp.return_value = client
    provider = SmtpMailProvider(_mail_config())

    def refuse_all(message):
        return {"hr@acme.com": (550, b"refused")}

    client.send_message = refuse_all

    with pytest.raises(MailSendError, match="refused recipients"):
        provider.send(
            MailMessage(
                to=["hr@acme.com"],
                subject="Application",
                body_text="Hello",
            )
        )
