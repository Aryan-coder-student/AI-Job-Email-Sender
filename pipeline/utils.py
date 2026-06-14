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
    if explicit_email and explicit_email.strip():
        return explicit_email.strip()

    for record in companies:
        if str(record.get("company_name") or "").strip().lower() == company_name.strip().lower():
            hr_email = str(record.get("hr_email") or "").strip()
            if hr_email:
                return hr_email

    if parsed_resume is not None:
        for email in parsed_resume.links.emails:
            cleaned = str(email).strip()
            if cleaned:
                return cleaned

    raise PipelineConfigurationError(
        "No recipient email found. Pass recipient_email or ensure resume links.emails is populated."
    )
