from __future__ import annotations

from celery import Celery

from app.celery.bootstrap import CELERY_APP_NAME, configure_celery
from app.celery.config import CeleryConfig

_config = CeleryConfig.from_env()

celery_app = Celery(CELERY_APP_NAME)
configure_celery(celery_app, _config)
