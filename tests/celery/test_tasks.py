from __future__ import annotations

from unittest.mock import patch

import pytest

import app.modules.emails.tasks  # noqa: F401
import app.modules.graph.tasks  # noqa: F401
import app.modules.mail.tasks  # noqa: F401
import app.modules.matching.tasks  # noqa: F401
from app.celery.app import celery_app


@pytest.fixture(autouse=True)
def eager_celery() -> None:
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True


@pytest.mark.parametrize(
    ("task_name", "patch_target", "kwargs", "return_value"),
    [
        pytest.param(
            "app.modules.graph.tasks.build_knowledge_graph_task",
            "app.modules.graph.tasks.task.run_build_knowledge_graph",
            {
                "resume": "resume.json",
                "github": "github.json",
                "companies": "companies.json",
            },
            {"candidate": {}, "companies": {}, "vector_index": {}},
            id="graph",
        ),
        pytest.param(
            "app.modules.matching.tasks.rank_applications_task",
            "app.modules.matching.tasks.task.run_rank_applications",
            {
                "companies": "companies.json",
                "company": "Acme",
                "candidate_id": "candidate:test",
            },
            [{"project_name": "demo"}],
            id="matching",
        ),
        pytest.param(
            "app.modules.emails.tasks.generate_draft_task",
            "app.modules.emails.tasks.task.run_generate_draft",
            {
                "resume": "resume.json",
                "company_name": "Acme",
                "matches": [{"project_name": "demo"}],
            },
            {"draft_id": "draft-1", "status": "queued"},
            id="emails",
        ),
        pytest.param(
            "app.modules.mail.tasks.process_email_queue_task",
            "app.modules.mail.tasks.task.run_process_email_queue",
            {"limit": 1, "dry_run": True},
            [{"draft_id": "draft-1", "status": "dry_run"}],
            id="mail",
        ),
    ],
)
def test_celery_task_delegates_to_runner(
    task_name: str,
    patch_target: str,
    kwargs: dict[str, object],
    return_value: object,
) -> None:
    with patch(patch_target) as run_mock:
        run_mock.return_value = return_value
        result = celery_app.tasks[task_name].apply(kwargs=kwargs)

        assert result.successful()
        run_mock.assert_called_once_with(**kwargs)
        assert result.result == return_value
