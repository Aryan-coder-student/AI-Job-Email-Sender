from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.modules.resume.model import ParsedResume, ResumeLinks
from pipeline.context import PipelineContext
from pipeline.exceptions import PipelineConfigurationError
from pipeline.utils import resolve_recipient_email


def test_resolve_recipient_email_prefers_explicit_value() -> None:
    email = resolve_recipient_email(
        company_name="Acme",
        companies=[{"company_name": "Acme", "hr_email": "hr@acme.com"}],
        parsed_resume=None,
        explicit_email="custom@example.com",
    )

    assert email == "custom@example.com"


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
    companies_file = tmp_path / "companies.json"
    companies_file.write_text('[{"company_name": "Acme"}]\n', encoding="utf-8")
    context.companies_path = companies_file
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


def test_load_artifact_state_requires_companies_path(tmp_path: Path) -> None:
    context = PipelineContext(output_dir=tmp_path)
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

    with pytest.raises(PipelineConfigurationError, match="companies_path"):
        context.load_artifact_state(from_step=5)
