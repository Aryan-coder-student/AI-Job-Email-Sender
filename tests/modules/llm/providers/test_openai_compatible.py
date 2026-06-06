from __future__ import annotations

import pytest

from app.core.exceptions import LLMConfigurationError
from app.modules.llm.interface import LLMMessage, LLMRequest
from app.modules.llm.providers.openai import OpenAIProvider


def test_openai_provider_requires_api_key() -> None:
    provider = OpenAIProvider(api_key=None)

    with pytest.raises(LLMConfigurationError, match="API key is not configured"):
        provider.generate(make_request())


def test_openai_provider_defaults() -> None:
    provider = OpenAIProvider()
    assert provider.name == "openai"
    assert provider.default_model == "gpt-4o-mini"
    assert provider.base_url is None
    assert provider.timeout_seconds == 60


def test_openai_provider_convert_messages() -> None:
    provider = OpenAIProvider(api_key="key")
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


def make_request() -> LLMRequest:
    return LLMRequest(
        messages=[
            LLMMessage(role="system", content="Be useful."),
            LLMMessage(role="user", content="Hello"),
        ],
        max_tokens=100,
    )
