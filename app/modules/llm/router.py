from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.core.exceptions import LLMError, LLMRateLimitError
from app.modules.llm.interface import LLMProvider, LLMRequest, LLMResponse


@dataclass
class LLMProviderState:
    paused_until: datetime | None = None
    last_error: str | None = None

    def is_paused(self, now: datetime | None = None) -> bool:
        active_now = now or datetime.now(timezone.utc)
        return self.paused_until is not None and self.paused_until > active_now


class LLMRouter:
    def __init__(
        self,
        providers: list[LLMProvider],
        *,
        default_rate_limit_pause_seconds: int = 60,
    ) -> None:
        if not providers:
            raise ValueError("LLMRouter requires at least one provider.")

        self.providers = providers
        self.default_rate_limit_pause_seconds = default_rate_limit_pause_seconds
        self.provider_states = {
            provider.name: LLMProviderState()
            for provider in providers
        }

    def generate(self, request: LLMRequest) -> LLMResponse:
        request.validate()
        last_error: Exception | None = None

        for provider in self.providers:
            state = self.provider_states[provider.name]

            if state.is_paused():
                continue

            try:
                return provider.generate(request)
            except LLMRateLimitError as error:
                last_error = error
                self.pause_provider(provider.name, error.retry_after_seconds)
                state.last_error = str(error)
                continue
            except LLMError as error:
                last_error = error
                state.last_error = str(error)
                continue

        if last_error:
            raise last_error

        raise LLMError("No LLM providers are currently available.")

    def pause_provider(
        self,
        provider_name: str,
        retry_after_seconds: int | None = None,
    ) -> None:
        pause_seconds = retry_after_seconds or self.default_rate_limit_pause_seconds
        self.provider_states[provider_name].paused_until = (
            datetime.now(timezone.utc) + timedelta(seconds=pause_seconds)
        )

    def reset_provider(self, provider_name: str) -> None:
        self.provider_states[provider_name] = LLMProviderState()
