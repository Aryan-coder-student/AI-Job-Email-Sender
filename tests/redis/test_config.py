from __future__ import annotations

import pytest

from app.core.exceptions import RedisConfigurationError
from app.redis.config import RedisConfig


def test_validate_rejects_empty_redis_url() -> None:
    config = RedisConfig(
        redis_url="  ",
        email_queue_key="email:queue:pending",
        send_rate_limit=10,
        send_rate_window_seconds=60,
    )

    with pytest.raises(RedisConfigurationError, match="REDIS_URL"):
        config.validate()


def test_validate_rejects_empty_queue_key() -> None:
    config = RedisConfig(
        redis_url="redis://localhost:6379/2",
        email_queue_key="",
        send_rate_limit=10,
        send_rate_window_seconds=60,
    )

    with pytest.raises(RedisConfigurationError, match="EMAIL_QUEUE_KEY"):
        config.validate()
