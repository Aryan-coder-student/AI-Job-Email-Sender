from __future__ import annotations

from typing import Any

import redis

from app.core.exceptions import RedisOperationError
from app.redis.config import RedisConfig


class RedisClientProvider:
    name = "redis"

    def __init__(self, config: RedisConfig) -> None:
        self._client = redis.Redis.from_url(config.redis_url, decode_responses=True)

    def get(self, key: str) -> str | None:
        return self._execute("get", key)

    def set(self, key: str, value: str) -> None:
        self._execute("set", key, value)

    def rpush(self, key: str, value: str) -> None:
        self._execute("rpush", key, value)

    def lrange(self, key: str, start: int, end: int) -> list[str]:
        result = self._execute("lrange", key, start, end)
        return list(result or [])

    def lrem(self, key: str, count: int, value: str) -> None:
        self._execute("lrem", key, count, value)

    def zadd(self, key: str, mapping: dict[str, float]) -> None:
        self._execute("zadd", key, mapping)

    def expire(self, key: str, seconds: int) -> None:
        self._execute("expire", key, seconds)

    def pipeline(self) -> redis.client.Pipeline:
        return self._client.pipeline()

    def _execute(self, method_name: str, *args: Any) -> Any:
        method = getattr(self._client, method_name)
        try:
            return method(*args)
        except redis.RedisError as error:
            raise RedisOperationError(f"Redis {method_name} failed: {error}") from error
