from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.exceptions import MailConfigurationError
from app.core.settings import get_settings
from app.modules.mail.presets import SMTP_PRESETS, SUPPORTED_MAIL_PROVIDERS
from app.modules.mail.validator import validate_mail_config

DEFAULT_MAIL_PROVIDER = "gmail"
DEFAULT_SMTP_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class MailConfig:
    provider: str
    host: str
    port: int
    username: str
    password: str
    from_email: str
    use_tls: bool
    use_ssl: bool
    timeout_seconds: int = DEFAULT_SMTP_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls) -> MailConfig:
        settings = get_settings()
        provider = _normalize_provider(settings.mail_provider or DEFAULT_MAIL_PROVIDER)
        username = _required_value(settings.smtp_username, field_name="SMTP_USERNAME")
        password = _required_value(settings.smtp_password, field_name="SMTP_PASSWORD")
        from_email = _normalize_optional(settings.smtp_from_email) or username
        host, port, use_tls, use_ssl = _resolve_connection_settings(settings, provider)

        config = cls(
            provider=provider,
            host=host,
            port=port,
            username=username,
            password=password,
            from_email=from_email,
            use_tls=use_tls,
            use_ssl=use_ssl,
            timeout_seconds=settings.smtp_timeout_seconds or DEFAULT_SMTP_TIMEOUT_SECONDS,
        )
        config.validate()
        return config

    def validate(self) -> None:
        validate_mail_config(self)


def _resolve_connection_settings(settings: Any, provider: str) -> tuple[str, int, bool, bool]:
    if provider == "custom":
        return (
            _required_value(settings.smtp_host, field_name="SMTP_HOST"),
            _parse_port(settings.smtp_port),
            settings.smtp_use_tls,
            settings.smtp_use_ssl,
        )

    preset = SMTP_PRESETS[provider]
    host = _normalize_optional(settings.smtp_host) or preset.host
    port = _parse_port(settings.smtp_port or preset.port)
    use_tls = settings.smtp_use_tls if settings.smtp_host else preset.use_tls
    use_ssl = settings.smtp_use_ssl if settings.smtp_host else preset.use_ssl
    return host, port, use_tls, use_ssl


def _normalize_provider(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MailConfigurationError("MAIL_PROVIDER must be a non-empty string.")

    provider = value.strip().lower()
    if provider not in SUPPORTED_MAIL_PROVIDERS:
        supported = ", ".join(SUPPORTED_MAIL_PROVIDERS)
        raise MailConfigurationError(f"Unsupported MAIL_PROVIDER. Use one of: {supported}.")

    return provider


def _required_value(value: Any, *, field_name: str) -> str:
    normalized = _normalize_optional(value)
    if not normalized:
        raise MailConfigurationError(f"{field_name} is required.")
    return normalized


def _normalize_optional(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _parse_port(value: Any) -> int:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise MailConfigurationError("SMTP_PORT is required for custom mail providers.")

    try:
        port = int(value)
    except (TypeError, ValueError) as error:
        raise MailConfigurationError("SMTP_PORT must be a valid integer.") from error

    if port < 1 or port > 65535:
        raise MailConfigurationError("SMTP_PORT must be between 1 and 65535.")

    return port
