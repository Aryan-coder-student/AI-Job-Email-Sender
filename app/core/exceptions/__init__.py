from app.core.exceptions.base import AppError
from app.core.exceptions.email import (
    EmailConfigurationError,
    EmailDraftError,
    EmailError,
    EmailQueueError,
)
from app.core.exceptions.graph import GraphConfigurationError, GraphError, GraphQueryError
from app.core.exceptions.llm import (
    LLMConfigurationError,
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
)
from app.core.exceptions.mail import MailConfigurationError, MailError, MailSendError
from app.core.exceptions.matching import MatchingError
from app.core.exceptions.parse import InvalidExcelError, InvalidGitHubError, InvalidResumeError
from app.core.exceptions.redis import RedisConfigurationError, RedisError, RedisOperationError
from app.core.exceptions.vector import VectorConfigurationError, VectorError

__all__ = [
    "AppError",
    "EmailConfigurationError",
    "EmailDraftError",
    "EmailError",
    "EmailQueueError",
    "GraphConfigurationError",
    "GraphError",
    "GraphQueryError",
    "InvalidExcelError",
    "InvalidGitHubError",
    "InvalidResumeError",
    "LLMConfigurationError",
    "LLMError",
    "LLMProviderError",
    "LLMRateLimitError",
    "MailConfigurationError",
    "MailError",
    "MailSendError",
    "MatchingError",
    "RedisConfigurationError",
    "RedisError",
    "RedisOperationError",
    "VectorConfigurationError",
    "VectorError",
]
