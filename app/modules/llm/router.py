from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.core.exceptions import LLMError, LLMRateLimitError
from app.core.logger import get_logger
from app.modules.llm.interface import LLMProvider, LLMRequest, LLMResponse

logger = get_logger(__name__)


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
        self._state_lock = threading.Lock()

    def generate(self, request: LLMRequest) -> LLMResponse:
        request.validate()
        last_error: Exception | None = None

        for provider in self.providers:
            if self._is_provider_paused(provider.name):
                continue

            try:
                return self._generate_with_provider(provider, request)
            except LLMRateLimitError as error:
                last_error = error
                self._handle_rate_limit(provider.name, error)
            except LLMError as error:
                last_error = error
                self._record_provider_error(provider.name, error)

        self._raise_generate_failure(last_error)

    def _is_provider_paused(self, provider_name: str) -> bool:
        with self._state_lock:
            is_paused = self.provider_states[provider_name].is_paused()

        if is_paused:
            logger.debug("Skipping paused LLM provider=%s", provider_name)

        return is_paused

    def _generate_with_provider(
        self,
        provider: LLMProvider,
        request: LLMRequest,
    ) -> LLMResponse:
        response = provider.generate(request)
        logger.debug(
            "LLM request succeeded provider=%s model=%s",
            response.provider,
            response.model,
        )
        return response

    def _handle_rate_limit(self, provider_name: str, error: LLMRateLimitError) -> None:
        logger.warning(
            "LLM provider rate limited provider=%s retry_after=%s",
            provider_name,
            error.retry_after_seconds,
        )
        with self._state_lock:
            self.pause_provider(provider_name, error.retry_after_seconds)
            self.provider_states[provider_name].last_error = str(error)

    def _record_provider_error(self, provider_name: str, error: LLMError) -> None:
        logger.warning("LLM provider failed provider=%s error=%s", provider_name, error)
        with self._state_lock:
            self.provider_states[provider_name].last_error = str(error)

    def _raise_generate_failure(self, last_error: Exception | None) -> None:
        if last_error:
            logger.error("All LLM providers failed last_error=%s", last_error)
            raise last_error

        logger.error("No LLM providers are currently available")
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
        with self._state_lock:
            self.provider_states[provider_name] = LLMProviderState()
