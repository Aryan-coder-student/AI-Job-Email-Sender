class AppError(Exception):
    """Base application exception."""


class InvalidExcelError(AppError):
    """Raised when an Excel file cannot be downloaded, opened, or parsed."""


class InvalidResumeError(AppError):
    """Raised when a resume file cannot be validated, opened, or parsed."""


class InvalidGitHubError(AppError):
    """Raised when GitHub URL/username is invalid or API fetch fails."""


class LLMError(AppError):
    """Base error for LLM provider and router failures."""


class LLMConfigurationError(LLMError):
    """Raised when an LLM provider is missing required configuration."""


class LLMProviderError(LLMError):
    """Raised when an LLM provider returns an unexpected error."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        status_code: int | None = None,
        response_body: str | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.response_body = response_body


class LLMRateLimitError(LLMProviderError):
    """Raised when an LLM provider returns a rate-limit response."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        status_code: int | None = 429,
        response_body: str | None = None,
        retry_after_seconds: int | None = None,
    ) -> None:
        super().__init__(
            message,
            provider=provider,
            status_code=status_code,
            response_body=response_body,
        )
        self.retry_after_seconds = retry_after_seconds
