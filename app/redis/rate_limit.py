from __future__ import annotations

import time

from app.core.exceptions import RedisOperationError
from app.redis.interface import RedisClient


class RedisRateLimiter:
    def __init__(self, client: RedisClient, *, key_prefix: str = "rate_limit") -> None:
        self._client = client
        self._key_prefix = key_prefix

    def allow(self, key: str, *, limit: int, window_seconds: int) -> bool:
        if limit < 1:
            raise ValueError("limit must be at least 1.")
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1.")

        redis_key = f"{self._key_prefix}:{key}"
        now = time.time()
        window_start = now - window_seconds

        try:
            pipe = self._client.pipeline()
            pipe.zremrangebyscore(redis_key, 0, window_start)
            pipe.zcard(redis_key)
            _, count = pipe.execute()
            if int(count) >= limit:
                return False
            self._client.zadd(redis_key, {str(now): now})
            self._client.expire(redis_key, window_seconds)
        except RedisOperationError as error:
            raise RedisOperationError(f"Rate limit check failed for {key}: {error}") from error

        return True
