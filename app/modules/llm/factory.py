from __future__ import annotations

import os

from app.modules.llm.providers.gemini import GeminiProvider
from app.modules.llm.providers.groq import GroqProvider
from app.modules.llm.providers.openai import OpenAIProvider
from app.modules.llm.router import LLMRouter

_GROQ_KEY_ENV_VARS = [
    "GROQ_API_KEY_1",
    "GROQ_API_KEY_2",
    "GROQ_API_KEY_3",
    "GROQ_API_KEY_4",
]


def build_default_llm_router() -> LLMRouter:
    groq_model = os.getenv("GROQ_MODEL", GroqProvider.default_model)

    providers = []
    for index, env_var in enumerate(_GROQ_KEY_ENV_VARS, start=1):
        api_key = os.getenv(env_var)
        if api_key:
            providers.append(
                GroqProvider(
                    name=f"groq-{index}",
                    api_key=api_key,
                    default_model=groq_model,
                )
            )

    # OpenAI: single key fallback
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        providers.append(
            OpenAIProvider(
                api_key=openai_key,
                default_model=os.getenv("OPENAI_MODEL", OpenAIProvider.default_model),
            )
        )

    # Gemini: single key fallback
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        providers.append(
            GeminiProvider(
                api_key=gemini_key,
                default_model=os.getenv("GEMINI_MODEL", GeminiProvider.default_model),
            )
        )

    if not providers:
        raise RuntimeError(
            "No LLM API keys found. Set at least one of: "
            + ", ".join(_GROQ_KEY_ENV_VARS)
            + ", OPENAI_API_KEY, GEMINI_API_KEY"
        )

    return LLMRouter(providers=providers)
