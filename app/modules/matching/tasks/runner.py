from __future__ import annotations

from pathlib import Path
from typing import Any

from app.modules.graph.serializers import load_json_file
from app.modules.llm.factory import build_default_llm_router
from app.modules.matching.ranker import rank_projects_for_employer


def run_rank_applications(
    *,
    companies: str | Path,
    company: str,
    candidate_id: str,
    job_url: str | None = None,
    top: int = 5,
) -> list[dict[str, Any]]:
    records = load_json_file(str(companies))
    matches = [
        record
        for record in records
        if str(record.get("company_name") or "").strip().lower() == company.strip().lower()
    ]
    if job_url:
        matches = [record for record in matches if record.get("job_url") == job_url]
    if not matches:
        raise ValueError(f"No company record found for {company}")

    ranked = rank_projects_for_employer(
        company_record=matches[0],
        candidate_id=candidate_id,
        llm_router=build_default_llm_router(),
        limit=top,
    )
    return [match.to_dict() for match in ranked]
