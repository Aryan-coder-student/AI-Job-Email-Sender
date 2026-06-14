from __future__ import annotations

from app.core.exceptions import (
    AppError,
    LLMProviderError,
    LLMRateLimitError,
    MailSendError,
    RedisConfigurationError,
    RedisOperationError,
)


def test_llm_provider_error_stores_metadata() -> None:
    error = LLMProviderError(
        "provider failed",
        provider="groq",
        status_code=502,
        response_body='{"detail":"bad gateway"}',
    )

    assert str(error) == "provider failed"
    assert error.provider == "groq"
    assert error.status_code == 502
    assert error.response_body == '{"detail":"bad gateway"}'


def test_llm_rate_limit_error_defaults_status_code() -> None:
    error = LLMRateLimitError("slow down", provider="gemini", retry_after_seconds=30)

    assert error.status_code == 429
    assert error.retry_after_seconds == 30


def test_mail_send_error_stores_provider() -> None:
    error = MailSendError("smtp failed", provider="smtp")

    assert str(error) == "smtp failed"
    assert error.provider == "smtp"


def test_redis_errors_inherit_from_app_error() -> None:
    config_error = RedisConfigurationError("missing url")
    operation_error = RedisOperationError("command failed")

    assert isinstance(config_error, AppError)
    assert isinstance(operation_error, AppError)
