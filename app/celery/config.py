from __future__ import annotations

from dataclasses import dataclass

from app.core.settings import get_settings

DEFAULT_CELERY_BROKER_URL = "redis://localhost:6379/0"
DEFAULT_CELERY_RESULT_BACKEND = "redis://localhost:6379/1"


@dataclass(frozen=True)
class CeleryConfig:
    broker_url: str
    result_backend: str

    @classmethod
    def from_env(cls) -> CeleryConfig:
        settings = get_settings()
        return cls(
            broker_url=settings.celery_broker_url or DEFAULT_CELERY_BROKER_URL,
            result_backend=settings.celery_result_backend or DEFAULT_CELERY_RESULT_BACKEND,
        )
