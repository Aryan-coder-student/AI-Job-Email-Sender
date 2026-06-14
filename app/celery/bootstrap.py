from __future__ import annotations

from celery import Celery

from app.celery.config import CeleryConfig

CELERY_APP_NAME = "job_send_crawl"

TASK_PACKAGES = [
    "app.modules.graph.tasks",
    "app.modules.emails.tasks",
    "app.modules.matching.tasks",
    "app.modules.mail.tasks",
]


def configure_celery(app: Celery, config: CeleryConfig) -> None:
    app.conf.update(
        broker_url=config.broker_url,
        result_backend=config.result_backend,
        task_track_started=True,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
    )
    app.autodiscover_tasks(TASK_PACKAGES)
