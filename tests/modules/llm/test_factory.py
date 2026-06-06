from __future__ import annotations

import pytest

from app.modules.llm.factory import build_default_llm_router


def test_factory_creates_all_providers(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY_1", "groq-key-1")
    monkeypatch.setenv("GROQ_API_KEY_2", "groq-key-2")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")

    router = build_default_llm_router()

    names = [p.name for p in router.providers]
    assert names == ["groq-1", "groq-2", "openai", "gemini"]


def test_factory_four_groq_keys(monkeypatch) -> None:
    for i in range(1, 5):
        monkeypatch.setenv(f"GROQ_API_KEY_{i}", f"key-{i}")

    router = build_default_llm_router()

    groq_providers = [p for p in router.providers if p.name.startswith("groq")]
    assert len(groq_providers) == 4
    assert groq_providers[0].api_key == "key-1"
    assert groq_providers[3].api_key == "key-4"


def test_factory_only_gemini_key(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")

    router = build_default_llm_router()

    assert len(router.providers) == 1
    assert router.providers[0].name == "gemini"
    assert router.providers[0].api_key == "gemini-key"


def test_factory_only_openai_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

    router = build_default_llm_router()

    assert len(router.providers) == 1
    assert router.providers[0].name == "openai"


def test_factory_respects_custom_models(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY_1", "key")
    monkeypatch.setenv("GROQ_MODEL", "custom-groq-model")

    router = build_default_llm_router()

    assert router.providers[0].default_model == "custom-groq-model"


def test_factory_raises_when_no_keys(monkeypatch) -> None:
    # Clear all possible keys
    for var in ["GROQ_API_KEY_1", "GROQ_API_KEY_2", "GROQ_API_KEY_3",
                "GROQ_API_KEY_4", "OPENAI_API_KEY", "GEMINI_API_KEY"]:
        monkeypatch.delenv(var, raising=False)

    with pytest.raises(RuntimeError, match="No LLM API keys found"):
        build_default_llm_router()
