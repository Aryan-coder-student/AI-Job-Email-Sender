from __future__ import annotations

import json
from typing import Any

from app.modules.github.model import (
    GitHubTechStack,
    ParsedGitHubProfile,
    ParsedGitHubProject,
)
from app.modules.resume.model import (
    ParsedResume,
    ResumeExperience,
    ResumeLinks,
    ResumeProject,
)


def parsed_resume_from_dict(payload: dict[str, Any]) -> ParsedResume:
    links_payload = payload.get("links") or {}
    links = ResumeLinks(
        emails=list(links_payload.get("emails") or []),
        phones=list(links_payload.get("phones") or []),
        github=links_payload.get("github"),
        linkedin=links_payload.get("linkedin"),
        portfolio=links_payload.get("portfolio"),
        urls=list(links_payload.get("urls") or []),
    )
    experience = [
        ResumeExperience(
            company_name=item.get("company_name"),
            date=item.get("date"),
            description=item.get("description"),
        )
        for item in payload.get("experience") or []
    ]
    projects = [
        ResumeProject(
            project_name=item.get("project_name"),
            link=item.get("link"),
            description=item.get("description"),
        )
        for item in payload.get("projects") or []
    ]
    return ParsedResume(
        filename=payload.get("filename"),
        file_extension=str(payload.get("file_extension") or ""),
        raw_text=str(payload.get("raw_text") or ""),
        candidate_name=payload.get("candidate_name"),
        summary=str(payload.get("summary") or ""),
        skills=list(payload.get("skills") or []),
        experience=experience,
        projects=projects,
        courses=[],
        certifications=[],
        achievements=list(payload.get("achievements") or []),
        research=list(payload.get("research") or []),
        education=list(payload.get("education") or []),
        links=links,
        metadata=dict(payload.get("metadata") or {}),
    )


def parsed_github_from_dict(payload: dict[str, Any]) -> ParsedGitHubProfile:
    projects = []
    for item in payload.get("projects") or []:
        tech_stack_payload = item.get("tech_stack") or {}
        projects.append(
            ParsedGitHubProject(
                repo_name=str(item.get("repo_name") or ""),
                repo_link=str(item.get("repo_link") or ""),
                deployed_link=item.get("deployed_link"),
                summary=str(item.get("summary") or ""),
                tech_stack=GitHubTechStack(
                    backend=list(tech_stack_payload.get("backend") or []),
                    frontend=list(tech_stack_payload.get("frontend") or []),
                    ai_ml=list(tech_stack_payload.get("ai_ml") or []),
                ),
                non_tech_tags=list(item.get("non_tech_tags") or []),
                raw_readme=str(item.get("raw_readme") or ""),
            )
        )
    return ParsedGitHubProfile(
        github_username=str(payload.get("github_username") or ""),
        github_url=str(payload.get("github_url") or ""),
        projects=projects,
        metadata=dict(payload.get("metadata") or {}),
    )


def load_json_file(path: str) -> Any:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)
