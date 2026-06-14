from __future__ import annotations

from typing import Any

from app.celery.app import celery_app
from app.modules.matching.tasks.runner import run_rank_applications


@celery_app.task(
    bind=True,
    name="app.modules.matching.tasks.rank_applications_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def rank_applications_task(self, **kwargs: Any) -> list[dict[str, Any]]:
    return run_rank_applications(**kwargs)
