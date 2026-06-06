from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.exceptions import LLMConfigurationError, LLMProviderError
from app.modules.llm.interface import LLMMessage, LLMRequest, LLMResponse


@dataclass
class GeminiProvider:
    name: str = "gemini"
    api_key: str | None = None
    default_model: str = "gemini-2.5-flash"
    timeout_seconds: int = 60

    def generate(self, request: LLMRequest) -> LLMResponse:
        if not self.api_key:
            raise LLMConfigurationError("Gemini API key is not configured.")

        model_name = request.model or self.default_model

        try:
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=self.api_key,
                temperature=request.temperature,
                max_output_tokens=request.max_tokens,
                timeout=self.timeout_seconds,
            )

            langchain_messages = self._convert_messages(request.messages)
            response: AIMessage = llm.invoke(langchain_messages)

        except Exception as error:
            raise LLMProviderError(
                f"Gemini API request failed: {error}",
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
