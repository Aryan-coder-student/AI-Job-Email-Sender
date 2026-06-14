from __future__ import annotations

from typing import Any

from app.celery.app import celery_app
from app.modules.graph.tasks.runner import run_build_knowledge_graph


@celery_app.task(
    bind=True,
    name="app.modules.graph.tasks.build_knowledge_graph_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def build_knowledge_graph_task(self, **kwargs: Any) -> dict[str, Any]:
    return run_build_knowledge_graph(**kwargs)
