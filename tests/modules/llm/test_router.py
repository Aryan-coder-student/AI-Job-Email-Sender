from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.core.exceptions import LLMError, LLMProviderError, LLMRateLimitError
from app.modules.llm.interface import LLMMessage, LLMRequest, LLMResponse
from app.modules.llm.router import LLMProviderState, LLMRouter


class FakeProvider:
    def __init__(self, name: str, result: LLMResponse | Exception) -> None:
        self.name = name
        self.default_model = f"{name}-model"
        self.result = result
        self.calls = 0

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1

        if isinstance(self.result, Exception):
            raise self.result

        return self.result


def test_router_requires_provider() -> None:
    with pytest.raises(ValueError, match="requires at least one provider"):
        LLMRouter([])


def test_provider_state_is_paused() -> None:
    now = datetime.now(timezone.utc)

    assert LLMProviderState(paused_until=now + timedelta(seconds=5)).is_paused(now)
    assert not LLMProviderState(paused_until=now - timedelta(seconds=5)).is_paused(now)


def test_router_returns_first_available_response() -> None:
    response = LLMResponse(content="ok", provider="one", model="one-model")
    provider = FakeProvider("one", response)
    router = LLMRouter([provider])

    result = router.generate(make_request())

    assert result is response
    assert provider.calls == 1


def test_router_pauses_rate_limited_provider_and_falls_back() -> None:
    groq = FakeProvider(
        "groq",
        LLMRateLimitError(
            "rate limit",
            provider="groq",
            retry_after_seconds=5,
        ),
    )
    openai_response = LLMResponse(content="fallback", provider="openai", model="model")
    openai = FakeProvider("openai", openai_response)
    router = LLMRouter([groq, openai])

    result = router.generate(make_request())

    assert result is openai_response
    assert groq.calls == 1
    assert openai.calls == 1
    assert router.provider_states["groq"].is_paused()


def test_router_skips_paused_provider() -> None:
    groq_response = LLMResponse(content="groq", provider="groq", model="model")
    openai_response = LLMResponse(content="openai", provider="openai", model="model")
    groq = FakeProvider("groq", groq_response)
    openai = FakeProvider("openai", openai_response)
    router = LLMRouter([groq, openai])
    router.pause_provider("groq", retry_after_seconds=10)

    result = router.generate(make_request())

    assert result is openai_response
    assert groq.calls == 0
    assert openai.calls == 1


def test_router_continues_after_provider_error() -> None:
    bad_provider = FakeProvider(
        "bad",
        LLMProviderError("bad failed", provider="bad"),
    )
    good_response = LLMResponse(content="ok", provider="good", model="model")
    good_provider = FakeProvider("good", good_response)
    router = LLMRouter([bad_provider, good_provider])

    result = router.generate(make_request())

    assert result is good_response
    assert router.provider_states["bad"].last_error == "bad failed"


def test_router_raises_last_error_when_all_providers_fail() -> None:
    router = LLMRouter(
        [
            FakeProvider("one", LLMProviderError("one failed", provider="one")),
            FakeProvider("two", LLMProviderError("two failed", provider="two")),
        ]
    )

    with pytest.raises(LLMProviderError, match="two failed"):
        router.generate(make_request())


def test_router_raises_when_all_providers_paused() -> None:
    provider = FakeProvider(
        "one",
        LLMResponse(content="ok", provider="one", model="model"),
    )
    router = LLMRouter([provider])
    router.pause_provider("one", retry_after_seconds=10)

    with pytest.raises(LLMError, match="No LLM providers are currently available"):
        router.generate(make_request())


def test_router_reset_provider() -> None:
    provider = FakeProvider(
        "one",
        LLMResponse(content="ok", provider="one", model="model"),
    )
    router = LLMRouter([provider])
    router.pause_provider("one", retry_after_seconds=10)

    router.reset_provider("one")

    assert not router.provider_states["one"].is_paused()


def make_request() -> LLMRequest:
    return LLMRequest(messages=[LLMMessage(role="user", content="Hello")])
