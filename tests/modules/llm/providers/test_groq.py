from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage

from app.core.exceptions import LLMConfigurationError
from app.modules.llm.interface import LLMMessage, LLMRequest
from app.modules.llm.providers.groq import GroqProvider


def test_groq_provider_requires_api_key() -> None:
    provider = GroqProvider(api_key=None)

    with pytest.raises(LLMConfigurationError, match="API key is not configured"):
        provider.generate(make_request())


def test_groq_provider_defaults() -> None:
    provider = GroqProvider()
    assert provider.name == "groq"
    assert provider.default_model == "llama-3.3-70b-versatile"
    assert provider.timeout_seconds == 60


def test_groq_provider_custom_name() -> None:
    provider = GroqProvider(name="groq-2", api_key="key")
    assert provider.name == "groq-2"


def test_groq_provider_convert_messages() -> None:
    provider = GroqProvider(api_key="key")
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


def test_groq_provider_convert_empty_messages() -> None:
    provider = GroqProvider(api_key="key")

    langchain_msgs = provider._convert_messages([])

    assert langchain_msgs == []


def test_groq_provider_passes_response_format_to_langchain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_kwargs: dict[str, object] = {}

    class FakeChatGroq:
        def __init__(self, **kwargs: object) -> None:
            captured_kwargs.update(kwargs)

        def invoke(self, messages: object) -> AIMessage:
            return AIMessage(content="{}")

    monkeypatch.setattr("app.modules.llm.providers.groq.ChatGroq", FakeChatGroq)

    provider = GroqProvider(api_key="key")
    provider.generate(
        LLMRequest(
            messages=[LLMMessage(role="user", content="Return JSON.")],
            response_format={"type": "json_object"},
        )
    )

    assert captured_kwargs["model_kwargs"] == {
        "response_format": {"type": "json_object"}
    }


def make_request() -> LLMRequest:
    return LLMRequest(
        messages=[
            LLMMessage(role="system", content="Be useful."),
            LLMMessage(role="user", content="Hello"),
        ],
        max_tokens=100,
    )
