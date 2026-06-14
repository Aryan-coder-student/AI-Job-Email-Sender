from __future__ import annotations

import pytest

from app.core.settings import reset_settings
from app.modules.llm.factory import build_default_llm_router

LLM_ENV_VARS = (
    "GROQ_API_KEY_1",
    "GROQ_API_KEY_2",
    "GROQ_API_KEY_3",
    "GROQ_API_KEY_4",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
)


def _clear_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in LLM_ENV_VARS:
        monkeypatch.setenv(var, "")
    reset_settings()


def test_factory_creates_all_providers(monkeypatch) -> None:
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("GROQ_API_KEY_1", "groq-key-1")
    monkeypatch.setenv("GROQ_API_KEY_2", "groq-key-2")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    reset_settings()

    router = build_default_llm_router()

    names = [p.name for p in router.providers]
    assert names == ["groq-1", "groq-2", "openai", "gemini"]


def test_factory_four_groq_keys(monkeypatch) -> None:
    _clear_llm_env(monkeypatch)
    for index in range(1, 5):
        monkeypatch.setenv(f"GROQ_API_KEY_{index}", f"key-{index}")
    reset_settings()

    router = build_default_llm_router()

    groq_providers = [p for p in router.providers if p.name.startswith("groq")]
    assert len(groq_providers) == 4
    assert groq_providers[0].api_key == "key-1"
    assert groq_providers[3].api_key == "key-4"


def test_factory_only_gemini_key(monkeypatch) -> None:
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    reset_settings()

    router = build_default_llm_router()

    assert len(router.providers) == 1
    assert router.providers[0].name == "gemini"
    assert router.providers[0].api_key == "gemini-key"


def test_factory_only_openai_key(monkeypatch) -> None:
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    reset_settings()

    router = build_default_llm_router()

    assert len(router.providers) == 1
    assert router.providers[0].name == "openai"


def test_factory_respects_custom_models(monkeypatch) -> None:
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("GROQ_API_KEY_1", "key")
    monkeypatch.setenv("GROQ_MODEL", "custom-groq-model")
    reset_settings()

    router = build_default_llm_router()

    assert router.providers[0].default_model == "custom-groq-model"


def test_factory_raises_when_no_keys(monkeypatch) -> None:
    _clear_llm_env(monkeypatch)

    with pytest.raises(RuntimeError, match="No LLM API keys found"):
        build_default_llm_router()
