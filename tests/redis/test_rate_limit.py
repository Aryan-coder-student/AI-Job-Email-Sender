from app.redis.rate_limit import RedisRateLimiter
from tests.redis.fakes import FakeRedis


def test_rate_limiter_allows_until_limit() -> None:
    client = FakeRedis()
    limiter = RedisRateLimiter(client)

    assert limiter.allow("email_send", limit=2, window_seconds=60) is True
    assert limiter.allow("email_send", limit=2, window_seconds=60) is True
    assert limiter.allow("email_send", limit=2, window_seconds=60) is False
