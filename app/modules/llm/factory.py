from __future__ import annotations

from app.core.logger import get_logger
from app.modules.llm.providers.gemini import GeminiProvider
from app.modules.llm.providers.groq import GroqProvider
from app.modules.llm.providers.openai import OpenAIProvider
from app.modules.llm.router import LLMRouter
from setting import GROQ_KEY_ENV_VARS, get_env

logger = get_logger(__name__)


def build_default_llm_router() -> LLMRouter:
    groq_model = get_env("GROQ_MODEL", GroqProvider.default_model)
    openai_key = get_env("OPENAI_API_KEY")
    gemini_key = get_env("GEMINI_API_KEY")

    providers = []
    for index, env_var in enumerate(GROQ_KEY_ENV_VARS, start=1):
        api_key = get_env(env_var)
        if api_key:
            providers.append(
                GroqProvider(
                    name=f"groq-{index}",
                    api_key=api_key,
                    default_model=groq_model,
                )
            )

    # OpenAI: single key fallback
    if openai_key:
        providers.append(
            OpenAIProvider(
                api_key=openai_key,
                default_model=get_env("OPENAI_MODEL", OpenAIProvider.default_model),
            )
        )

    if gemini_key:
        providers.append(
            GeminiProvider(
                api_key=gemini_key,
                default_model=get_env("GEMINI_MODEL", GeminiProvider.default_model),
            )
        )

    if not providers:
        logger.error("No LLM API keys configured")
        raise RuntimeError(
            "No LLM API keys found. Set at least one of: "
            + ", ".join(GROQ_KEY_ENV_VARS)
            + ", OPENAI_API_KEY, GEMINI_API_KEY"
        )

    provider_names = [provider.name for provider in providers]
    logger.info("Initialized LLM router providers=%s", provider_names)
    return LLMRouter(providers=providers)
