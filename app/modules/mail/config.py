from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.exceptions import MailConfigurationError
from app.modules.mail.presets import SMTP_PRESETS, SUPPORTED_MAIL_PROVIDERS
from app.modules.mail.validator import validate_mail_config
from setting import (
    MAIL_PROVIDER_ENV,
    SMTP_FROM_EMAIL_ENV,
    SMTP_HOST_ENV,
    SMTP_PASSWORD_ENV,
    SMTP_PORT_ENV,
    SMTP_TIMEOUT_SECONDS_ENV,
    SMTP_USE_SSL_ENV,
    SMTP_USE_TLS_ENV,
    SMTP_USERNAME_ENV,
    get_env,
)

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
        provider = _normalize_provider(get_env(MAIL_PROVIDER_ENV, DEFAULT_MAIL_PROVIDER))
        username = _required_env(SMTP_USERNAME_ENV)
        password = _required_env(SMTP_PASSWORD_ENV)
        from_email = _normalize_optional(get_env(SMTP_FROM_EMAIL_ENV)) or username

        host, port, use_tls, use_ssl = _resolve_connection_settings(provider)

        config = cls(
            provider=provider,
            host=host,
            port=port,
            username=username,
            password=password,
            from_email=from_email,
            use_tls=use_tls,
            use_ssl=use_ssl,
            timeout_seconds=_parse_timeout(get_env(SMTP_TIMEOUT_SECONDS_ENV, str(DEFAULT_SMTP_TIMEOUT_SECONDS))),
        )
        config.validate()
        return config

    def validate(self) -> None:
        validate_mail_config(self)


def _resolve_connection_settings(provider: str) -> tuple[str, int, bool, bool]:
    if provider == "custom":
        return (
            _required_env(SMTP_HOST_ENV),
            _parse_port(get_env(SMTP_PORT_ENV)),
            _parse_bool(get_env(SMTP_USE_TLS_ENV, "true")),
            _parse_bool(get_env(SMTP_USE_SSL_ENV, "false")),
        )

    preset = SMTP_PRESETS[provider]
    return (
        _normalize_optional(get_env(SMTP_HOST_ENV)) or preset.host,
        _parse_port(get_env(SMTP_PORT_ENV, str(preset.port))),
        _parse_bool(get_env(SMTP_USE_TLS_ENV, str(preset.use_tls).lower())),
        _parse_bool(get_env(SMTP_USE_SSL_ENV, str(preset.use_ssl).lower())),
    )


def _normalize_provider(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MailConfigurationError("MAIL_PROVIDER must be a non-empty string.")

    provider = value.strip().lower()
    if provider not in SUPPORTED_MAIL_PROVIDERS:
        supported = ", ".join(SUPPORTED_MAIL_PROVIDERS)
        raise MailConfigurationError(f"Unsupported MAIL_PROVIDER. Use one of: {supported}.")

    return provider


def _required_env(name: str) -> str:
    value = _normalize_optional(get_env(name))
    if not value:
        raise MailConfigurationError(f"{name} is required.")
    return value


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


def _parse_timeout(value: Any) -> int:
    try:
        timeout = int(value)
    except (TypeError, ValueError) as error:
        raise MailConfigurationError("SMTP_TIMEOUT_SECONDS must be a valid integer.") from error

    if timeout < 1:
        raise MailConfigurationError("SMTP_TIMEOUT_SECONDS must be at least 1.")

    return timeout


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if not isinstance(value, str):
        raise MailConfigurationError("Boolean SMTP settings must be true or false.")

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    raise MailConfigurationError("Boolean SMTP settings must be true or false.")
