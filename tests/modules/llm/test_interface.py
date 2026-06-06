from __future__ import annotations

import pytest

from app.modules.llm.interface import LLMMessage, LLMRequest, LLMResponse


def test_llm_message_to_dict() -> None:
    message = LLMMessage(role="user", content="Hello")

    assert message.to_dict() == {
        "role": "user",
        "content": "Hello",
    }


def test_llm_request_validate_accepts_valid_request() -> None:
    request = LLMRequest(messages=[LLMMessage(role="user", content="Hello")])

    request.validate()


@pytest.mark.parametrize(
    ("llm_request", "message"),
    [
        (
            LLMRequest(messages=[]),
            "must contain at least one message",
        ),
        (
            LLMRequest(messages=[LLMMessage(role="user", content=" ")]),
            "cannot be empty",
        ),
        (
            LLMRequest(
                messages=[LLMMessage(role="user", content="Hello")],
                temperature=3,
            ),
            "temperature must be between 0 and 2",
        ),
        (
            LLMRequest(
                messages=[LLMMessage(role="user", content="Hello")],
                max_tokens=0,
            ),
            "max_tokens must be at least 1",
        ),
    ],
)
def test_llm_request_validate_rejects_invalid_request(
    llm_request: LLMRequest,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        llm_request.validate()


def test_llm_response_defaults() -> None:
    response = LLMResponse(content="Hi", provider="fake", model="fake-model")

    assert response.usage == {}
    assert response.raw_response == {}
