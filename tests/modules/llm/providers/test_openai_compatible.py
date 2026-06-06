from __future__ import annotations

import pytest

from app.core.exceptions import LLMConfigurationError, LLMProviderError
from app.modules.llm.interface import LLMMessage, LLMRequest
from app.modules.llm.providers import openai_compatible
from app.modules.llm.providers.openai import OpenAIProvider


def test_openai_compatible_provider_requires_api_key() -> None:
    provider = OpenAIProvider(api_key=None)

    with pytest.raises(LLMConfigurationError, match="API key is not configured"):
        provider.generate(make_request())


def test_openai_compatible_provider_generates(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}

    def fake_post_json(**kwargs):
        calls.update(kwargs)
        return (
            {
                "model": "gpt-test",
                "choices": [
                    {
                        "message": {"content": "Hello"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 12},
            },
            {},
        )

    monkeypatch.setattr(openai_compatible, "post_json", fake_post_json)
    provider = OpenAIProvider(api_key="key", default_model="gpt-test")

    response = provider.generate(make_request())

    assert response.content == "Hello"
    assert response.provider == "openai"
    assert response.model == "gpt-test"
    assert response.finish_reason == "stop"
    assert response.usage == {"total_tokens": 12}
    assert calls["url"] == "https://api.openai.com/v1/chat/completions"
    assert calls["headers"] == {"Authorization": "Bearer key"}
    assert calls["payload"] == {
        "model": "gpt-test",
        "messages": [
            {"role": "system", "content": "Be useful."},
            {"role": "user", "content": "Hello"},
        ],
        "temperature": 0.3,
        "max_tokens": 100,
    }


def test_openai_compatible_provider_supports_response_format() -> None:
    provider = OpenAIProvider(api_key="key")
    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
        response_format={"type": "json_object"},
    )

    payload = provider._build_payload(request, "model")

    assert payload["response_format"] == {"type": "json_object"}


def test_openai_compatible_provider_rejects_bad_response_shape() -> None:
    provider = OpenAIProvider(api_key="key")

    with pytest.raises(LLMProviderError, match="unexpected response shape"):
        provider._parse_response({"choices": []}, "model")


def make_request() -> LLMRequest:
    return LLMRequest(
        messages=[
            LLMMessage(role="system", content="Be useful."),
            LLMMessage(role="user", content="Hello"),
        ],
        max_tokens=100,
    )
