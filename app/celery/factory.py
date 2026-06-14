from __future__ import annotations

from celery import Celery

from app.celery.app import celery_app
from app.celery.bootstrap import CELERY_APP_NAME, configure_celery
from app.celery.config import CeleryConfig


def build_celery_app(config: CeleryConfig | None = None) -> Celery:
    active_config = config or CeleryConfig.from_env()
    app = Celery(CELERY_APP_NAME)
    configure_celery(app, active_config)
    return app


def build_default_celery_app() -> Celery:
    return celery_app
