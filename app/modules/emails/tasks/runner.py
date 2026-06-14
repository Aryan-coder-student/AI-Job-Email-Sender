from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.exceptions import EmailDraftError
from app.modules.emails.factory import build_default_draft_service
from app.modules.emails.model import DraftGenerationRequest
from app.modules.emails.service import generate_application_draft
from app.modules.graph.serializers import load_json_file, parsed_resume_from_dict
from app.redis.factory import build_default_email_draft_queue
from app.redis.interface import EmailDraftQueue


def _resolve_company_record(
    *,
    company_name: str,
    company_record: dict[str, Any] | None,
    companies_path: str | Path | None,
    company_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if company_record is not None:
        return company_record

    if company_records is not None:
        records = company_records
    elif companies_path is not None:
        records = load_json_file(str(companies_path))
    else:
        raise EmailDraftError("company_record, company_records, or companies_path is required.")
    matches = [
        record
        for record in records
        if str(record.get("company_name") or "").strip().lower() == company_name.strip().lower()
    ]
    if not matches:
        raise EmailDraftError(f"No company record found for {company_name}")
    return matches[0]


def _resolve_matches(
    *,
    matches: list[dict[str, Any]] | None,
    matches_path: str | Path | None,
) -> list[dict[str, Any]]:
    if matches is not None:
        return matches
    if matches_path is None:
        raise EmailDraftError("matches or matches_path is required.")
    loaded = load_json_file(str(matches_path))
    if not isinstance(loaded, list):
        raise EmailDraftError("matches_path must contain a JSON array.")
    return loaded


def _load_github_projects(github_path: str | Path | None) -> list[dict[str, Any]]:
    if github_path is None:
        return []

    payload = load_json_file(str(github_path))
    if not isinstance(payload, dict):
        raise EmailDraftError("github_path must contain a JSON object.")
    projects = payload.get("projects")
    if not isinstance(projects, list):
        raise EmailDraftError("github_path must contain a projects array.")
    return projects


def run_generate_draft(
    *,
    resume: str | Path | None = None,
    parsed_resume_data: dict[str, Any] | None = None,
    company_name: str,
    matches: list[dict[str, Any]] | None = None,
    matches_path: str | Path | None = None,
    company_record: dict[str, Any] | None = None,
    companies_path: str | Path | None = None,
    company_records: list[dict[str, Any]] | None = None,
    github_path: str | Path | None = None,
    github_projects: list[dict[str, Any]] | None = None,
    recipient_email: str | None = None,
    enqueue: bool = True,
    queue: EmailDraftQueue | None = None,
) -> dict[str, Any]:
    if parsed_resume_data is not None:
        parsed_resume = parsed_resume_from_dict(parsed_resume_data)
    elif resume is not None:
        parsed_resume = parsed_resume_from_dict(load_json_file(str(resume)))
    else:
        raise EmailDraftError("resume path or parsed_resume_data is required.")

    resolved_matches = _resolve_matches(matches=matches, matches_path=matches_path)
    resolved_company = _resolve_company_record(
        company_name=company_name,
        company_record=company_record,
        companies_path=companies_path,
        company_records=company_records,
    )
    top_match = resolved_matches[0] if resolved_matches else {}
    active_github_projects = github_projects if github_projects is not None else _load_github_projects(github_path)

    request = DraftGenerationRequest(
        candidate_name=parsed_resume.candidate_name,
        candidate_summary=parsed_resume.summary,
        candidate_skills=parsed_resume.skills,
        company_name=company_name,
        company_record=resolved_company,
        top_match=top_match,
        recipient_email=recipient_email,
        github_projects=active_github_projects,
    )

    llm_router = build_default_draft_service()
    draft = generate_application_draft(request, llm_router=llm_router)

    if enqueue:
        active_queue = queue or build_default_email_draft_queue()
        active_queue.enqueue(draft)
        draft = draft.with_status("queued")

    return draft.to_dict()
