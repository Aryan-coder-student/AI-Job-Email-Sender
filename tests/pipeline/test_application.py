from __future__ import annotations

from pathlib import Path

import pytest

from app.modules.resume.model import ParsedResume, ResumeLinks
from pipeline.application import ApplicationPipeline
from pipeline.steps.base import BaseStepHandler
from pipeline.config import PipelineOptions
from pipeline.context import PipelineContext
from pipeline.exceptions import PipelineConfigurationError
from pipeline.types import PipelineStep
from pipeline.utils import resolve_recipient_email


def test_resolve_recipient_email_prefers_explicit_value() -> None:
    email = resolve_recipient_email(
        company_name="Acme",
        companies=[{"company_name": "Acme", "hr_email": "hr@acme.com"}],
        parsed_resume=None,
        explicit_email="custom@example.com",
    )

    assert email == "custom@example.com"


def test_resolve_recipient_email_uses_exact_company_email() -> None:
    email = resolve_recipient_email(
        company_name="Acme",
        companies=[{"company_name": "Acme", "hr_email": "hr@acme.com"}],
        parsed_resume=None,
        explicit_email=None,
    )

    assert email == "hr@acme.com"


def test_resolve_recipient_email_uses_resume_email_when_hr_missing() -> None:
    resume = ParsedResume(
        filename="resume.pdf",
        file_extension=".pdf",
        raw_text="text",
        candidate_name="Aryan",
        summary="",
        skills=[],
        experience=[],
        projects=[],
        courses=[],
        certifications=[],
        achievements=[],
        research=[],
        education=[],
        links=ResumeLinks(emails=["candidate@example.com"]),
    )

    email = resolve_recipient_email(
        company_name="Acme",
        companies=[{"company_name": "Acme"}],
        parsed_resume=resume,
        explicit_email=None,
    )

    assert email == "candidate@example.com"


def test_load_artifact_state_from_step_five(tmp_path: Path) -> None:
    context = PipelineContext(output_dir=tmp_path)
    context.companies = [{"company_name": "Acme"}]
    context.write_json(
        context.parsed_resume_path,
        {
            "filename": "resume.pdf",
            "file_extension": ".pdf",
            "raw_text": "text",
            "candidate_name": "Aryan",
            "summary": "",
            "skills": [],
            "experience": [],
            "projects": [],
            "achievements": [],
            "research": [],
            "education": [],
            "links": {"emails": ["candidate@example.com"]},
        },
    )
    context.write_json(
        context.github_projects_path,
        {"github_username": "user", "github_url": "https://github.com/user", "projects": []},
    )
    context.write_json(
        context.graph_result_path,
        {"candidate": {"metadata": {"candidate_id": "candidate:user"}}},
    )
    context.write_json(context.matches_path, [{"project_name": "demo"}])

    context.load_artifact_state(from_step=5)

    assert context.parsed_resume is not None
    assert context.parsed_github is not None
    assert context.companies == [{"company_name": "Acme"}]
    assert context.candidate_id == "candidate:user"
    assert context.matches == [{"project_name": "demo"}]


def test_load_artifact_state_does_not_load_companies(tmp_path: Path) -> None:
    context = PipelineContext(output_dir=tmp_path)
    companies = [{"company_name": "Builder Loaded"}]
    context.companies = companies
    context.write_json(
        context.parsed_resume_path,
        {
            "filename": "resume.pdf",
            "file_extension": ".pdf",
            "raw_text": "text",
            "candidate_name": "Aryan",
            "summary": "",
            "skills": [],
            "experience": [],
            "projects": [],
            "achievements": [],
            "research": [],
            "education": [],
            "links": {},
        },
    )
    context.write_json(
        context.github_projects_path,
        {"github_username": "user", "github_url": "https://github.com/user", "projects": []},
    )
    context.write_json(
        context.graph_result_path,
        {"candidate": {"metadata": {"candidate_id": "candidate:user"}}},
    )

    context.load_artifact_state(from_step=4)

    assert context.companies is companies


def test_pipeline_requires_builder_loaded_companies(tmp_path: Path) -> None:
    companies_file = tmp_path / "companies.json"
    companies_file.write_text('[{"company_name": "Acme"}]\n', encoding="utf-8")
    context = PipelineContext(companies_path=companies_file, output_dir=tmp_path)
    pipeline = ApplicationPipeline(
        context=context,
        options=PipelineOptions(
            steps=(PipelineStep.BUILD_GRAPH,),
            output_dir=tmp_path,
            skip_services=True,
        ),
        project_root=tmp_path,
    )

    with pytest.raises(PipelineConfigurationError, match="loaded by the builder"):
        pipeline.run()


def test_pipeline_run_notifies_step_observer(tmp_path: Path) -> None:
    observer = _RecordingStepObserver()
    pipeline = ApplicationPipeline(
        context=PipelineContext(resume_path=tmp_path / "resume.pdf", output_dir=tmp_path),
        options=PipelineOptions(
            steps=(PipelineStep.PARSE_RESUME, PipelineStep.PARSE_GITHUB),
            output_dir=tmp_path,
            skip_services=True,
        ),
        project_root=tmp_path,
        step_handlers={
            PipelineStep.PARSE_RESUME: _NoopStepHandler(),
            PipelineStep.PARSE_GITHUB: _NoopStepHandler(),
        },
    )

    result = pipeline.run(observer=observer)

    assert observer.events == [
        ("started", PipelineStep.PARSE_RESUME),
        ("completed", PipelineStep.PARSE_RESUME),
        ("started", PipelineStep.PARSE_GITHUB),
        ("completed", PipelineStep.PARSE_GITHUB),
    ]
    assert result.steps_executed == (
        PipelineStep.PARSE_RESUME.value,
        PipelineStep.PARSE_GITHUB.value,
    )


def test_pipeline_rejects_empty_explicit_steps(tmp_path: Path) -> None:
    pipeline = ApplicationPipeline(
        context=PipelineContext(output_dir=tmp_path),
        options=PipelineOptions(output_dir=tmp_path, skip_services=True),
        project_root=tmp_path,
        step_handlers={},
    )

    with pytest.raises(PipelineConfigurationError, match="At least one pipeline step"):
        pipeline.run(steps=())


class _NoopStepHandler(BaseStepHandler):
    step = PipelineStep.PARSE_RESUME
    requires_services = False

    def validate(self, context: PipelineContext, options: PipelineOptions) -> None:
        pass

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        return None


class _RecordingStepObserver:
    def __init__(self) -> None:
        self.events: list[tuple[str, PipelineStep]] = []

    def step_started(self, step: PipelineStep) -> None:
        self.events.append(("started", step))

    def step_completed(self, step: PipelineStep) -> None:
        self.events.append(("completed", step))
