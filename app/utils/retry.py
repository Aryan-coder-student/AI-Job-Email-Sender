from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from typing import TypeVar

T = TypeVar("T")


def compute_backoff_seconds(
    attempt: int,
    *,
    base_seconds: float = 1.0,
    max_seconds: float = 60.0,
) -> float:
    if attempt < 1:
        return base_seconds

    delay = base_seconds * (2 ** (attempt - 1))
    return min(delay, max_seconds)


def retry_call(
    func: Callable[[], T],
    *,
    max_attempts: int = 3,
    retryable_exceptions: Iterable[type[BaseException]] = (Exception,),
    base_backoff_seconds: float = 1.0,
    max_backoff_seconds: float = 60.0,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    last_error: BaseException | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except tuple(retryable_exceptions) as error:
            last_error = error
            if attempt >= max_attempts:
                break
            sleep(
                compute_backoff_seconds(
                    attempt,
                    base_seconds=base_backoff_seconds,
                    max_seconds=max_backoff_seconds,
                )
            )

    assert last_error is not None
    raise last_error
