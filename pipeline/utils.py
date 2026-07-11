from __future__ import annotations

from typing import Any

from app.modules.resume.model import ParsedResume
from pipeline.exceptions import PipelineConfigurationError


def resolve_recipient_email(
    *,
    company_name: str,
    companies: list[dict[str, Any]],
    parsed_resume: ParsedResume | None,
    explicit_email: str | None,
) -> str:
    return _first_available_email(
        (
            explicit_email,
            _company_hr_email(company_name=company_name, companies=companies),
            _resume_email(parsed_resume),
        )
    )


def _company_hr_email(*, company_name: str, companies: list[dict[str, Any]]) -> str | None:
    return next(
        (
            record["hr_email"]
            for record in companies
            if record.get("company_name") == company_name and record.get("hr_email")
        ),
        None,
    )


def _resume_email(parsed_resume: ParsedResume | None) -> str | None:
    return (
        next(iter(parsed_resume.links.emails), None)
        if parsed_resume is not None
        else None
    )


def _first_available_email(candidates: tuple[str | None, ...]) -> str:
    email = next((candidate for candidate in candidates if candidate), None)
    if email is not None:
        return email
    raise PipelineConfigurationError(
        "No recipient email found. Pass recipient_email or ensure resume links.emails is populated."
    )
