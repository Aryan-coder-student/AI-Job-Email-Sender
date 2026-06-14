from __future__ import annotations

from app.modules.mail.presets import SMTP_PRESETS


def test_gmail_preset_defaults() -> None:
    preset = SMTP_PRESETS["gmail"]

    assert preset.host == "smtp.gmail.com"
    assert preset.port == 587
    assert preset.use_tls is True
    assert preset.use_ssl is False


def test_outlook_preset_defaults() -> None:
    preset = SMTP_PRESETS["outlook"]

    assert preset.host == "smtp.office365.com"
    assert preset.port == 587
    assert preset.use_tls is True
    assert preset.use_ssl is False
