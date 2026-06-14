from __future__ import annotations

from app.core.settings import get_settings, reset_settings


def test_get_settings_reads_env(monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    reset_settings()

    settings = get_settings()

    assert settings.log_level == "DEBUG"


def test_groq_api_keys_skips_empty_values(monkeypatch) -> None:
    for index in range(1, 5):
        monkeypatch.setenv(f"GROQ_API_KEY_{index}", "")
    monkeypatch.setenv("GROQ_API_KEY_1", "key-one")
    reset_settings()

    assert get_settings().groq_api_keys() == ["key-one"]
