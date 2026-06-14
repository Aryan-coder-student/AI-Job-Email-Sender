from app.utils.retry import compute_backoff_seconds, retry_call


def test_compute_backoff_seconds() -> None:
    assert compute_backoff_seconds(1) == 1.0
    assert compute_backoff_seconds(2) == 2.0
    assert compute_backoff_seconds(3) == 4.0


def test_retry_call_retries_until_success() -> None:
    attempts = {"count": 0}

    def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("temporary")
        return "ok"

    result = retry_call(
        flaky,
        max_attempts=3,
        retryable_exceptions=(RuntimeError,),
        sleep=lambda _: None,
    )
    assert result == "ok"
    assert attempts["count"] == 3
