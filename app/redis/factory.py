from __future__ import annotations

from app.core.logger import get_logger
from app.redis.config import RedisConfig
from app.redis.interface import EmailDraftQueue, RateLimiter, RedisClient
from app.redis.providers.redis import RedisClientProvider
from app.redis.queues.email_draft import RedisEmailDraftQueue
from app.redis.rate_limit import RedisRateLimiter

logger = get_logger(__name__)


def build_redis_client(config: RedisConfig | None = None) -> RedisClient:
    active_config = config or RedisConfig.from_env()
    active_config.validate()
    client = RedisClientProvider(active_config)
    logger.info("Initialized redis client url=%s", active_config.redis_url)
    return client


def build_default_redis_client() -> RedisClient:
    return build_redis_client()


def build_rate_limiter(
    config: RedisConfig | None = None,
    client: RedisClient | None = None,
) -> RateLimiter:
    active_config = config or RedisConfig.from_env()
    active_client = client or build_redis_client(active_config)
    return RedisRateLimiter(active_client)


def build_default_rate_limiter() -> RateLimiter:
    return build_rate_limiter()


def build_email_draft_queue(
    config: RedisConfig | None = None,
    client: RedisClient | None = None,
) -> EmailDraftQueue:
    active_config = config or RedisConfig.from_env()
    active_config.validate()
    active_client = client or build_redis_client(active_config)
    queue = RedisEmailDraftQueue(active_config, active_client)
    logger.info("Initialized email draft queue key=%s", active_config.email_queue_key)
    return queue


def build_default_email_draft_queue() -> EmailDraftQueue:
    return build_email_draft_queue()
