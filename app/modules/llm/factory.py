from __future__ import annotations

from app.core.logger import get_logger
from app.core.settings import get_settings
from app.modules.llm.providers.gemini import GeminiProvider
from app.modules.llm.providers.groq import GroqProvider
from app.modules.llm.providers.openai import OpenAIProvider
from app.modules.llm.router import LLMRouter

logger = get_logger(__name__)


def build_default_llm_router() -> LLMRouter:
    settings = get_settings()
    groq_model = settings.groq_model or GroqProvider.default_model

    providers = []
    for index, api_key in enumerate(settings.groq_api_keys(), start=1):
        providers.append(
            GroqProvider(
                name=f"groq-{index}",
                api_key=api_key,
                default_model=groq_model,
            )
        )

    if settings.openai_api_key:
        providers.append(
            OpenAIProvider(
                api_key=settings.openai_api_key,
                default_model=settings.openai_model or OpenAIProvider.default_model,
            )
        )

    if settings.gemini_api_key:
        providers.append(
            GeminiProvider(
                api_key=settings.gemini_api_key,
                default_model=settings.gemini_model or GeminiProvider.default_model,
            )
        )

    if not providers:
        logger.error("No LLM API keys configured")
        raise RuntimeError(
            "No LLM API keys found. Set at least one of: "
            "GROQ_API_KEY_1, GROQ_API_KEY_2, GROQ_API_KEY_3, GROQ_API_KEY_4, "
            "OPENAI_API_KEY, GEMINI_API_KEY"
        )

    provider_names = [provider.name for provider in providers]
    logger.info("Initialized LLM router providers=%s", provider_names)
    return LLMRouter(providers=providers)
