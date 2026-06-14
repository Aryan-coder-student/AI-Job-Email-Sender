from __future__ import annotations

from typing import Any


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.lists: dict[str, list[str]] = {}
        self.sorted_sets: dict[str, dict[str, float]] = {}
        self.expiry: dict[str, int] = {}

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def set(self, key: str, value: str) -> None:
        self.values[key] = value

    def rpush(self, key: str, value: str) -> None:
        self.lists.setdefault(key, []).append(value)

    def lrange(self, key: str, start: int, end: int) -> list[str]:
        items = self.lists.get(key, [])
        if end == -1:
            return items[start:]
        return items[start : end + 1]

    def lrem(self, key: str, count: int, value: str) -> None:
        items = self.lists.get(key, [])
        if value in items:
            items.remove(value)

    def zadd(self, key: str, mapping: dict[str, float]) -> None:
        items = self.sorted_sets.setdefault(key, {})
        items.update(mapping)

    def expire(self, key: str, seconds: int) -> None:
        self.expiry[key] = seconds

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self)


class FakePipeline:
    def __init__(self, client: FakeRedis) -> None:
        self._client = client
        self._key = ""
        self._window_start = 0.0

    def zremrangebyscore(self, key: str, start: float, end: float) -> None:
        self._key = key
        self._window_start = end
        items = self._client.sorted_sets.setdefault(key, {})
        self._client.sorted_sets[key] = {
            member: score for member, score in items.items() if not (start <= score <= end)
        }

    def zcard(self, key: str) -> None:
        self._key = key

    def execute(self) -> list[Any]:
        return [None, len(self._client.sorted_sets.get(self._key, {}))]
