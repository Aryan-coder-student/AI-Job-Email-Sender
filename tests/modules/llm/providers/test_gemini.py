from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage

from app.core.exceptions import LLMConfigurationError
from app.modules.llm.interface import LLMMessage, LLMRequest
from app.modules.llm.providers.gemini import GeminiProvider


def test_gemini_provider_requires_api_key() -> None:
    provider = GeminiProvider(api_key=None)

    with pytest.raises(LLMConfigurationError, match="API key is not configured"):
        provider.generate(make_request())


def test_gemini_provider_defaults() -> None:
    provider = GeminiProvider()
    assert provider.name == "gemini"
    assert provider.default_model == "gemini-2.5-flash"
    assert provider.timeout_seconds == 60


def test_gemini_provider_convert_messages() -> None:
    provider = GeminiProvider(api_key="key")
    messages = [
        LLMMessage(role="system", content="Be useful."),
        LLMMessage(role="user", content="Hello"),
        LLMMessage(role="assistant", content="Hi there!"),
    ]

    langchain_msgs = provider._convert_messages(messages)

    assert len(langchain_msgs) == 3
    assert langchain_msgs[0].content == "Be useful."
    assert langchain_msgs[1].content == "Hello"
    assert langchain_msgs[2].content == "Hi there!"


def test_gemini_provider_convert_messages_preserves_order() -> None:
    provider = GeminiProvider(api_key="key")
    messages = [
        LLMMessage(role="user", content="First"),
        LLMMessage(role="assistant", content="Second"),
        LLMMessage(role="user", content="Third"),
    ]

    langchain_msgs = provider._convert_messages(messages)

    assert [msg.content for msg in langchain_msgs] == ["First", "Second", "Third"]


def test_gemini_provider_convert_empty_messages() -> None:
    provider = GeminiProvider(api_key="key")

    langchain_msgs = provider._convert_messages([])

    assert langchain_msgs == []


def test_gemini_provider_passes_json_response_mime_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_kwargs: dict[str, object] = {}

    class FakeChatGoogleGenerativeAI:
        def __init__(self, **kwargs: object) -> None:
            captured_kwargs.update(kwargs)

        def invoke(self, messages: object) -> AIMessage:
            return AIMessage(content="{}")

    monkeypatch.setattr(
        "app.modules.llm.providers.gemini.ChatGoogleGenerativeAI",
        FakeChatGoogleGenerativeAI,
    )

    provider = GeminiProvider(api_key="key")
    provider.generate(
        LLMRequest(
            messages=[LLMMessage(role="user", content="Return JSON.")],
            response_format={"type": "json_object"},
        )
    )

    assert captured_kwargs["response_mime_type"] == "application/json"


def make_request() -> LLMRequest:
    return LLMRequest(
        messages=[
            LLMMessage(role="system", content="Be useful."),
            LLMMessage(role="user", content="Hello"),
        ],
        max_tokens=100,
    )
