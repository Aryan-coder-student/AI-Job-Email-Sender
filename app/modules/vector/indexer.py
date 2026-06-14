from __future__ import annotations

from app.modules.github.model import ParsedGitHubProfile
from app.modules.vector.embeddings import (
    EmbeddingProvider,
    stable_point_id,
)
from app.modules.vector.interface import VectorStore


def build_employer_embedding_text(
    *,
    company_description: str | None,
    job_description: str | None,
    role: str | None,
) -> str:
    sections: list[str] = []
    if company_description:
        sections.append(f"Company: {company_description}")
    if role:
        sections.append(f"Role: {role}")
    if job_description:
        sections.append(f"Job Description: {job_description}")
    return "\n".join(sections)


def build_project_embedding_text(*, repo_name: str, summary: str, raw_readme: str) -> str:
    readme_excerpt = raw_readme[:4000]
    return f"Project: {repo_name}\nSummary: {summary}\nREADME:\n{readme_excerpt}"


def index_projects(
    parsed_github: ParsedGitHubProfile,
    *,
    vector_store: VectorStore,
    embedding_provider: EmbeddingProvider,
    collection: str,
) -> int:
    indexed = 0
    for project in parsed_github.projects:
        text = build_project_embedding_text(
            repo_name=project.repo_name,
            summary=project.summary,
            raw_readme=project.raw_readme,
        )
        vector = embedding_provider.embed(text)
        point_id = stable_point_id("project", project.repo_link)
        vector_store.upsert(
            collection,
            point_id=point_id,
            vector=vector,
            payload={
                "project_id": point_id,
                "repo_name": project.repo_name,
                "repo_link": project.repo_link,
                "summary": project.summary,
                "embedding_text": text,
            },
        )
        indexed += 1
    return indexed


def index_job_openings(
    company_records: list[dict],
    *,
    vector_store: VectorStore,
    embedding_provider: EmbeddingProvider,
    collection: str,
) -> int:
    indexed = 0
    for record in company_records:
        company_name = str(record.get("company_name") or "").strip()
        if not company_name:
            continue
        text = build_employer_embedding_text(
            company_description=record.get("company_description"),
            job_description=record.get("job_description"),
            role=record.get("role"),
        )
        if not text.strip():
            continue
        vector = embedding_provider.embed(text)
        key = f"{company_name}:{record.get('job_url') or record.get('source_row')}"
        point_id = stable_point_id("job", key)
        vector_store.upsert(
            collection,
            point_id=point_id,
            vector=vector,
            payload={
                "job_id": point_id,
                "company_name": company_name,
                "company_description": record.get("company_description"),
                "job_description": record.get("job_description"),
                "role": record.get("role"),
                "embedding_text": text,
            },
        )
        indexed += 1
    return indexed
