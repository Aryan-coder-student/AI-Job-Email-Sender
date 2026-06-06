from __future__ import annotations

from app.modules.llm.factory import build_default_llm_router


def test_build_default_llm_router_uses_environment(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setenv("GROQ_MODEL", "groq-model")
    monkeypatch.setenv("OPENAI_MODEL", "openai-model")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-model")

    router = build_default_llm_router()

    assert [provider.name for provider in router.providers] == [
        "groq",
        "openai",
        "gemini",
    ]
    assert router.providers[0].api_key == "groq-key"
    assert router.providers[1].api_key == "openai-key"
    assert router.providers[2].api_key == "gemini-key"
    assert router.providers[0].default_model == "groq-model"
    assert router.providers[1].default_model == "openai-model"
    assert router.providers[2].default_model == "gemini-model"
