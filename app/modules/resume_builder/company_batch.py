"""Generate a separate, immutable candidate resume for each company with ranked matches.

Artifacts live inside a single pipeline run directory. No global candidate profile
is overwritten, and no resume is sent to any recipient automatically.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from app.modules.resume_builder.latex import PdfLatexCompiler
from app.modules.resume_builder.model import JobRequirements, ProfileItem
from app.modules.resume_builder.repository import JsonResumeBuilderRepository
from app.modules.resume_builder.service import ResumeBuilderService, profile_from_pipeline_artifact


def company_key(company_name: str) -> str:
    """An opaque, filesystem-safe company identifier within a run."""
    return hashlib.sha256(company_name.strip().casefold().encode("utf-8")).hexdigest()[:20]


class CompanyResumeBatch:
    def __init__(self, output_dir: Path, compiler=None) -> None:
        self.output_dir = Path(output_dir)
        self.root = self.output_dir / "company_resumes"
        self.service = ResumeBuilderService(
            JsonResumeBuilderRepository(self.root),
            compiler or PdfLatexCompiler(),
            self.root / "compiled",
        )

    @property
    def manifest_path(self) -> Path:
        return self.output_dir / "company_resumes.json"

    def read_manifest(self) -> dict[str, dict[str, Any]]:
        if not self.manifest_path.exists():
            return {}
        payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}

    def get_entry(self, key: str) -> dict[str, Any] | None:
        return next(
            (entry for entry in self.read_manifest().values() if entry["company_key"] == key),
            None,
        )

    def generate(
        self,
        *,
        resume: dict[str, Any],
        github: dict[str, Any],
        companies: list[dict[str, Any]],
        matches: dict[str, list[dict[str, Any]]],
        limit: int = 5,
    ) -> dict[str, dict[str, Any]]:
        if not isinstance(matches, dict):
            raise ValueError("Ranked company matches are required.")
        original_profile = profile_from_pipeline_artifact(resume)
        available_projects = {
            str(project.get("repo_name") or "").casefold(): project
            for project in github.get("projects") or []
            if isinstance(project, dict)
        }
        entries: dict[str, dict[str, Any]] = {}
        for company in companies:
            name = str(company.get("company_name") or "").strip()
            ranked = matches.get(name) or []
            if not name or not ranked:
                continue
            if name in entries:
                raise ValueError(f"Duplicate company name in resume batch: {name}")

            relevant: list[ProfileItem] = []
            technologies: list[str] = []
            seen: set[str] = set()
            for match in ranked[:limit]:
                project_name = str(match.get("project_name") or "")
                project = available_projects.get(project_name.casefold())
                if project is None or project_name.casefold() in seen:
                    continue
                seen.add(project_name.casefold())
                stack = project.get("tech_stack") or {}
                skills = [
                    str(technology) for category in ("backend", "frontend", "ai_ml")
                    for technology in stack.get(category) or []
                ]
                technologies.extend(skills)
                relevant.append(ProfileItem(
                    title=project_name,
                    description=str(project.get("summary") or ""),
                    skills=skills,
                    link=project.get("repo_link"),
                ))

            # Each company gets a private snapshot; never save it as the shared profile.
            scoped_profile = original_profile.model_copy(deep=True)
            if relevant:
                scoped_profile.projects = relevant
            job = JobRequirements(
                company_name=name,
                role=str(company.get("role") or ""),
                description=str(company.get("job_description") or company.get("company_description") or ""),
                required_skills=list(dict.fromkeys(technologies)),
            )
            document = self.service.create_document(
                job, "jvs", max(5, min(limit, 10)), profile=scoped_profile,
            )
            pdf = self.service.pdf(document)
            if not pdf.startswith(b"%PDF-"):
                raise ValueError(f"Unable to compile PDF resume for {name}")
            entries[name] = {
                "company_name": name,
                "company_key": company_key(name),
                "document_id": document.id,
                "role": job.role,
                "match_count": len(ranked),
                "status": "ready",
            }

        self.output_dir.mkdir(parents=True, exist_ok=True)
        pending = self.manifest_path.with_suffix(".json.tmp")
        pending.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        pending.replace(self.manifest_path)
        return entries
