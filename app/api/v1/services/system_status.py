from __future__ import annotations

from typing import Any

from app.core.settings import get_settings


def build_system_status() -> dict[str, Any]:
    settings = get_settings()

    llm_providers = {
        "groq": {
            "configured": bool(settings.groq_api_keys()),
            "key_count": len(settings.groq_api_keys()),
            "model": settings.groq_model or "default",
        },
        "openai": {
            "configured": bool(settings.openai_api_key),
            "model": settings.openai_model or "default",
        },
        "gemini": {
            "configured": bool(settings.gemini_api_key),
            "model": settings.gemini_model or "default",
        },
    }

    services = {
        "redis": {
            "configured": bool(settings.redis_url),
            "url": settings.redis_url,
        },
        "neo4j": {
            "configured": bool(settings.neo4j_uri and settings.neo4j_user),
            "url": settings.neo4j_uri,
        },
        "qdrant": {
            "configured": bool(settings.qdrant_url),
            "url": settings.qdrant_url,
        },
        "mail": {
            "configured": _mail_configured(settings),
            "provider": settings.mail_provider,
            "from_email": settings.smtp_from_email or settings.smtp_username,
        },
        "github": {
            "configured": bool(settings.github_token),
        },
    }

    return {
        "llm": {
            "configured": any(provider["configured"] for provider in llm_providers.values()),
            "providers": llm_providers,
        },
        "services": services,
        "dry_run_available": True,
    }


def _mail_configured(settings: Any) -> bool:
    return bool(
        settings.smtp_host
        and settings.smtp_username
        and settings.smtp_password
    )
