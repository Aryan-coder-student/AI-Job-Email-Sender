from __future__ import annotations

from app.modules.vector.indexer import (
    build_employer_embedding_text,
    build_project_embedding_text,
)


def test_build_employer_embedding_text_includes_company_and_job_sections() -> None:
    text = build_employer_embedding_text(
        company_description="AI startup",
        job_description="Need LangChain experience",
        role="AI Engineer",
    )
    assert "Company: AI startup" in text
    assert "Role: AI Engineer" in text
    assert "Job Description: Need LangChain experience" in text


def test_build_project_embedding_text_includes_summary() -> None:
    text = build_project_embedding_text(
        repo_name="AI-Job-Email-Sender",
        summary="Email automation",
        raw_readme="README body",
    )
    assert "AI-Job-Email-Sender" in text
    assert "Email automation" in text
