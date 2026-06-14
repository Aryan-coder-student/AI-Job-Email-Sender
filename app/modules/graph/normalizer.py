from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse

from app.modules.graph.ontology import load_ontology

SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    normalized = value.strip().lower()
    slug = SLUG_PATTERN.sub("_", normalized).strip("_")
    return slug or "unknown"


def normalize_technology(value: str) -> str:
    ontology = load_ontology()
    key = value.strip().lower()
    return ontology.technology_aliases.get(key, slugify(value))


def normalize_capability(value: str) -> str:
    ontology = load_ontology()
    key = value.strip().lower()
    return ontology.capability_aliases.get(key, slugify(value))


def normalize_domain(value: str) -> str:
    return slugify(value)


def normalize_role(value: str) -> str:
    return slugify(value)


def build_candidate_id(*, github_url: str | None = None, email: str | None = None, name: str | None = None) -> str:
    if github_url:
        username = github_url.rstrip("/").split("/")[-1]
        return f"candidate:{slugify(username)}"
    if email:
        return f"candidate:{slugify(email)}"
    if name:
        return f"candidate:{slugify(name)}"
    raise ValueError("Candidate id requires github_url, email, or name.")


def build_project_id(repo_link: str) -> str:
    parsed = urlparse(repo_link)
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return f"project:{path.lower()}"


def build_company_id(*, company_name: str, company_url: str | None = None) -> str:
    if company_url:
        host = urlparse(company_url).netloc or company_url
        return f"company:{slugify(host)}"
    return f"company:{slugify(company_name)}"


def build_job_id(*, company_id: str, job_url: str | None, source_row: int | None = None) -> str:
    if job_url:
        digest = hashlib.sha1(job_url.encode("utf-8")).hexdigest()[:12]
        return f"job:{company_id.split(':', 1)[-1]}:{digest}"
    if source_row is not None:
        return f"job:{company_id.split(':', 1)[-1]}:row_{source_row}"
    digest = hashlib.sha1(company_id.encode("utf-8")).hexdigest()[:12]
    return f"job:{company_id.split(':', 1)[-1]}:{digest}"


def build_role_id(role: str) -> str:
    return f"role:{normalize_role(role)}"


def build_technology_id(value: str) -> str:
    return f"technology:{normalize_technology(value)}"


def build_capability_id(value: str) -> str:
    return f"capability:{normalize_capability(value)}"


def build_domain_id(value: str) -> str:
    return f"domain:{normalize_domain(value)}"


def build_ontology_term_id(category: str, slug: str) -> str:
    return f"term:{category}:{slug}"


def project_repo_slug(repo_link: str | None, project_name: str | None) -> str | None:
    if repo_link:
        path = urlparse(repo_link).path.strip("/")
        if path:
            return path.split("/")[-1].lower()
    if project_name:
        return slugify(project_name)
    return None


def links_match_project(resume_link: str | None, repo_link: str) -> bool:
    resume_slug = project_repo_slug(resume_link, None)
    repo_slug = project_repo_slug(repo_link, None)
    if resume_slug and repo_slug and resume_slug == repo_slug:
        return True
    if resume_link and resume_link.rstrip("/") == repo_link.rstrip("/"):
        return True
    return False
