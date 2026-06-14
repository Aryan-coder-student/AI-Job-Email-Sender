from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions import RedisConfigurationError
from app.core.settings import get_settings

DEFAULT_REDIS_URL = "redis://localhost:6379/2"
DEFAULT_EMAIL_QUEUE_KEY = "email:queue:pending"


@dataclass(frozen=True)
class RedisConfig:
    redis_url: str
    email_queue_key: str
    send_rate_limit: int
    send_rate_window_seconds: int

    @classmethod
    def from_env(cls) -> RedisConfig:
        settings = get_settings()
        return cls(
            redis_url=settings.redis_url or DEFAULT_REDIS_URL,
            email_queue_key=settings.email_queue_key or DEFAULT_EMAIL_QUEUE_KEY,
            send_rate_limit=settings.email_send_rate_limit,
            send_rate_window_seconds=settings.email_send_rate_window_seconds,
        )

    def validate(self) -> None:
        if not self.redis_url.strip():
            raise RedisConfigurationError("REDIS_URL is required.")
        if not self.email_queue_key.strip():
            raise RedisConfigurationError("EMAIL_QUEUE_KEY is required.")
