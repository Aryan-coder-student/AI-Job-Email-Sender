from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


LLMRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class LLMMessage:
    role: LLMRole
    content: str

    def to_dict(self) -> dict[str, str]:
        return {
            "role": self.role,
            "content": self.content,
        }


@dataclass(frozen=True)
class LLMRequest:
    messages: list[LLMMessage]
    model: str | None = None
    temperature: float | None = 0.3
    max_tokens: int | None = None
    response_format: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.messages:
            raise ValueError("LLMRequest.messages must contain at least one message.")

        for message in self.messages:
            if not message.content.strip():
                raise ValueError("LLM messages cannot be empty.")

        if self.temperature is not None and not 0 <= self.temperature <= 2:
            raise ValueError("temperature must be between 0 and 2.")

        if self.max_tokens is not None and self.max_tokens < 1:
            raise ValueError("max_tokens must be at least 1.")


@dataclass(frozen=True)
class LLMResponse:
    content: str
    provider: str
    model: str
    finish_reason: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    raw_response: dict[str, Any] = field(default_factory=dict)


class LLMProvider(Protocol):
    name: str
    default_model: str

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a single non-streaming text response."""
