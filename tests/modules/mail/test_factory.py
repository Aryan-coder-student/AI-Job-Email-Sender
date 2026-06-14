from __future__ import annotations

from unittest.mock import patch

from app.modules.mail.config import MailConfig
from app.modules.mail.factory import build_default_mail_sender


def _mail_config() -> MailConfig:
    return MailConfig(
        provider="gmail",
        host="smtp.gmail.com",
        port=587,
        username="user@gmail.com",
        password="app-password",
        from_email="user@gmail.com",
        use_tls=True,
        use_ssl=False,
    )


@patch("app.modules.mail.factory.SmtpMailProvider")
@patch("app.modules.mail.factory.MailConfig.from_env")
def test_build_default_mail_sender_wires_provider(mock_from_env, mock_provider_cls) -> None:
    mock_from_env.return_value = _mail_config()
    mock_provider = mock_provider_cls.return_value
    mock_provider.name = "gmail"

    sender = build_default_mail_sender()

    mock_from_env.assert_called_once()
    mock_provider_cls.assert_called_once()
    assert sender.provider is mock_provider
