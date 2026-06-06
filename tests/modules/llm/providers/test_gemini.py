from __future__ import annotations

import pytest

from app.core.exceptions import LLMConfigurationError, LLMProviderError
from app.modules.llm.interface import LLMMessage, LLMRequest
from app.modules.llm.providers import gemini
from app.modules.llm.providers.gemini import GeminiProvider


def test_gemini_provider_requires_api_key() -> None:
    provider = GeminiProvider(api_key=None)

    with pytest.raises(LLMConfigurationError, match="API key is not configured"):
        provider.generate(make_request())


def test_gemini_provider_generates(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}

    def fake_post_json(**kwargs):
        calls.update(kwargs)
        return (
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "Hello"}, {"text": " there"}],
                        },
                        "finishReason": "STOP",
                    }
                ],
                "usageMetadata": {"totalTokenCount": 11},
            },
            {},
        )

    monkeypatch.setattr(gemini, "post_json", fake_post_json)
    provider = GeminiProvider(api_key="key", default_model="gemini-test")

    response = provider.generate(make_request())

    assert response.content == "Hello there"
    assert response.provider == "gemini"
    assert response.model == "gemini-test"
    assert response.finish_reason == "STOP"
    assert response.usage == {"totalTokenCount": 11}
    assert calls["url"] == (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-test:generateContent"
    )
    assert calls["headers"] == {"x-goog-api-key": "key"}
    assert calls["payload"] == {
        "contents": [
            {"role": "user", "parts": [{"text": "Hello"}]},
            {"role": "model", "parts": [{"text": "Hi"}]},
        ],
        "systemInstruction": {
            "parts": [{"text": "Be useful."}],
        },
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 100,
        },
    }


def test_gemini_provider_supports_multiple_system_messages() -> None:
    provider = GeminiProvider(api_key="key")
    instruction = provider._system_instruction(
        [
            LLMMessage(role="system", content="One"),
            LLMMessage(role="system", content="Two"),
            LLMMessage(role="user", content="Hello"),
        ]
    )

    assert instruction == "One\n\nTwo"


def test_gemini_provider_rejects_bad_response_shape() -> None:
    provider = GeminiProvider(api_key="key")

    with pytest.raises(LLMProviderError, match="unexpected response shape"):
        provider._parse_response({"candidates": []}, "model")


def make_request() -> LLMRequest:
    return LLMRequest(
        messages=[
            LLMMessage(role="system", content="Be useful."),
            LLMMessage(role="user", content="Hello"),
            LLMMessage(role="assistant", content="Hi"),
        ],
        max_tokens=100,
    )
