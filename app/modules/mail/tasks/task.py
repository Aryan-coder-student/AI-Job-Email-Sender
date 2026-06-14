from __future__ import annotations

from typing import Any

from app.celery.app import celery_app
from app.modules.mail.tasks.runner import run_process_email_queue


@celery_app.task(
    bind=True,
    name="app.modules.mail.tasks.process_email_queue_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def process_email_queue_task(self, **kwargs: Any) -> list[dict[str, Any]]:
    return run_process_email_queue(**kwargs)
