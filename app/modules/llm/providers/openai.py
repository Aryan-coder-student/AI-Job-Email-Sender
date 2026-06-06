from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI

from app.core.exceptions import LLMConfigurationError, LLMProviderError
from app.modules.llm.interface import LLMMessage, LLMRequest, LLMResponse


@dataclass
class OpenAIProvider:
    name: str = "openai"
    api_key: str | None = None
    default_model: str = "gpt-4o-mini"
    base_url: str | None = None
    timeout_seconds: int = 60

    def generate(self, request: LLMRequest) -> LLMResponse:
        if not self.api_key:
            raise LLMConfigurationError(f"{self.name} API key is not configured.")

        model_name = request.model or self.default_model

        try:
            llm = ChatOpenAI(
                model=model_name,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                timeout=self.timeout_seconds,
                model_kwargs=request.response_format
                and {"response_format": request.response_format}
                or {},
            )

            langchain_messages = self._convert_messages(request.messages)
            response: AIMessage = llm.invoke(langchain_messages)

        except Exception as error:
            raise LLMProviderError(
                f"{self.name} API request failed: {error}",
                provider=self.name,
            ) from error

        usage_metadata = response.usage_metadata or {}

        usage = {
            "promptTokenCount": usage_metadata.get("input_tokens", 0),
            "candidatesTokenCount": usage_metadata.get("output_tokens", 0),
            "totalTokenCount": usage_metadata.get("total_tokens", 0),
        }

        return LLMResponse(
            content=str(response.content),
            provider=self.name,
            model=model_name,
            finish_reason=response.response_metadata.get("finish_reason")
            if response.response_metadata
            else None,
            usage=usage,
            raw_response=response.dict(),
        )

    def _convert_messages(self, messages: list[LLMMessage]) -> list[BaseMessage]:
        langchain_messages: list[BaseMessage] = []
        for msg in messages:
            if msg.role == "system":
                langchain_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content))
        return langchain_messages
