from __future__ import annotations

from typing import Any

from app.celery.app import celery_app
from app.core.exceptions import EmailDraftError, LLMError
from app.modules.emails.tasks.runner import run_generate_draft


@celery_app.task(
    bind=True,
    name="app.modules.emails.tasks.generate_draft_task",
    autoretry_for=(LLMError, EmailDraftError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def generate_draft_task(self, **kwargs: Any) -> dict[str, Any]:
    return run_generate_draft(**kwargs)
