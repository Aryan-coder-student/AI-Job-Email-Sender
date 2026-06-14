from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SmtpPreset:
    host: str
    port: int
    use_tls: bool
    use_ssl: bool


SMTP_PRESETS: dict[str, SmtpPreset] = {
    "gmail": SmtpPreset(
        host="smtp.gmail.com",
        port=587,
        use_tls=True,
        use_ssl=False,
    ),
    "outlook": SmtpPreset(
        host="smtp.office365.com",
        port=587,
        use_tls=True,
        use_ssl=False,
    ),
}

SUPPORTED_MAIL_PROVIDERS = tuple(SMTP_PRESETS.keys()) + ("custom",)
