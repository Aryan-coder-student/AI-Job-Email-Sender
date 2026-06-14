from __future__ import annotations

import json
from typing import Any

from prompts.emails.draft import DRAFT_USER_PROMPT


def build_draft_user_prompt(
    *,
    candidate_name: str | None,
    candidate_summary: str | None,
    candidate_skills: list[str],
    company_name: str,
    company_description: str | None,
    job_description: str | None,
    role: str | None,
    top_match: dict[str, Any],
    format_instructions: str,
) -> str:
    return DRAFT_USER_PROMPT.format(
        candidate_name=candidate_name or "Unknown",
        candidate_summary=candidate_summary or "",
        candidate_skills_json=json.dumps(candidate_skills, ensure_ascii=False),
        company_name=company_name,
        company_description=company_description or "",
        job_description=job_description or "",
        role=role or "",
        project_name=top_match.get("project_name"),
        explanation=top_match.get("explanation"),
        graph_score=top_match.get("graph_score"),
        embedding_score=top_match.get("embedding_score"),
        llm_score=top_match.get("llm_score"),
        graph_paths_json=json.dumps(top_match.get("paths", []), ensure_ascii=False),
        format_instructions=format_instructions,
    )
