from __future__ import annotations

import re
from typing import Any

_PROJECT_NAME_PATTERN = re.compile(r"[^a-z0-9]+")


def normalize_project_name(name: str) -> str:
    normalized = _PROJECT_NAME_PATTERN.sub("_", name.strip().lower()).strip("_")
    return normalized or "unknown"


def resolve_public_link(project: dict[str, Any]) -> str | None:
    deployed_link = str(project.get("deployed_link") or "").strip()
    if deployed_link:
        return deployed_link

    repo_link = str(project.get("repo_link") or "").strip()
    return repo_link or None


def find_github_project(
    project_name: str | None,
    github_projects: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not project_name:
        return None

    target = normalize_project_name(project_name)
    for project in github_projects:
        repo_name = str(project.get("repo_name") or "")
        if normalize_project_name(repo_name) == target:
            return project
    return None


def order_projects_for_email(
    *,
    github_projects: list[dict[str, Any]],
    top_match: dict[str, Any],
) -> list[dict[str, Any]]:
    if not github_projects:
        return []

    top_project = find_github_project(
        str(top_match.get("project_name") or "") or None,
        github_projects,
    )
    if top_project is None:
        return list(github_projects)

    seen_links = {str(top_project.get("repo_link") or "")}
    ordered = [top_project]
    for project in github_projects:
        repo_link = str(project.get("repo_link") or "")
        if repo_link in seen_links:
            continue
        seen_links.add(repo_link)
        ordered.append(project)
    return ordered


def format_project_links_section(
    *,
    github_projects: list[dict[str, Any]],
    top_match: dict[str, Any],
) -> str:
    lines: list[str] = []
    for project in order_projects_for_email(
        github_projects=github_projects,
        top_match=top_match,
    ):
        link = resolve_public_link(project)
        if not link:
            continue
        repo_name = str(project.get("repo_name") or "Project").strip()
        lines.append(f"- {repo_name}: {link}")

    if not lines:
        return ""

    return "GitHub project links:\n" + "\n".join(lines)


def append_github_links_to_body(
    body_text: str,
    *,
    github_projects: list[dict[str, Any]],
    top_match: dict[str, Any],
) -> str:
    links_section = format_project_links_section(
        github_projects=github_projects,
        top_match=top_match,
    )
    if not links_section:
        return body_text

    return f"{body_text.rstrip()}\n\n{links_section}"


def append_github_links_to_html(
    body_html: str | None,
    *,
    github_projects: list[dict[str, Any]],
    top_match: dict[str, Any],
) -> str | None:
    if body_html is None:
        return None

    items: list[str] = []
    for project in order_projects_for_email(
        github_projects=github_projects,
        top_match=top_match,
    ):
        link = resolve_public_link(project)
        if not link:
            continue
        repo_name = str(project.get("repo_name") or "Project").strip()
        items.append(f'<li><a href="{link}">{repo_name}</a></li>')

    if not items:
        return body_html

    links_html = (
        f'{body_html.rstrip()}<p><strong>GitHub project links:</strong></p>'
        f"<ul>{''.join(items)}</ul>"
    )
    return links_html
