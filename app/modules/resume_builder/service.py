from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from app.modules.resume_builder.interface import LatexCompiler, ResumeBuilderRepository
from app.modules.resume_builder.latex import LatexRenderer, PdfLatexCompiler
from app.modules.resume_builder.matcher import KeywordRecommendationEngine
from app.modules.resume_builder.model import JobRequirements, LatexUpdateRequest, ProfessionalProfile, ResumeDocument
from app.modules.resume_builder.model import ProfileItem
from app.modules.resume_builder.repository import JsonResumeBuilderRepository


class ResumeBuilderService:
    def __init__(self, repository: ResumeBuilderRepository, compiler: LatexCompiler, output_dir: Path) -> None:
        self.repository = repository
        self.compiler = compiler
        self.output_dir = output_dir
        self.matcher = KeywordRecommendationEngine()
        self.renderer = LatexRenderer()

    def get_profile(self) -> ProfessionalProfile:
        return self.repository.get_profile()

    def save_profile(self, profile: ProfessionalProfile) -> ProfessionalProfile:
        return self.repository.save_profile(profile)

    def recommend(self, job: JobRequirements, limit: int = 10):
        return self.matcher.recommend(self.get_profile(), job, limit)

    def create_document(self, job: JobRequirements, template: str, limit: int, source_latex: str | None = None) -> ResumeDocument:
        profile = self.get_profile()
        recommendations = self.matcher.recommend(profile, job, limit)
        document = ResumeDocument(
            company_name=job.company_name, role=job.role, template=template,
            profile=profile, recommendations=recommendations,
            selected_item_ids=[item.item_id for item in recommendations],
        )
        selected_projects = [item for item in profile.projects if item.id in document.selected_item_ids]
        base_source = source_latex or self.renderer.render(document)
        document.custom_latex = self.renderer.tailor_existing(
            base_source, company_name=job.company_name, role=job.role,
            projects=selected_projects,
            technical_keywords=job.required_skills,
            nontechnical_keywords=job.keywords,
        )
        return self.repository.save_document(document)

    def create_from_pipeline(
        self,
        *,
        source_latex: str,
        company: dict,
        github: dict,
        matches: list[dict],
        limit: int,
    ) -> ResumeDocument:
        matched_names = [str(item.get("project_name") or "") for item in matches[:limit]]
        projects_by_name = {str(item.get("repo_name") or "").lower(): item for item in github.get("projects") or []}
        projects: list[ProfileItem] = []
        technical: list[str] = []
        nontechnical: list[str] = []
        for name in matched_names:
            item = projects_by_name.get(name.lower())
            if not item:
                continue
            stack = item.get("tech_stack") or {}
            tech = [str(value) for group in ("backend", "frontend", "ai_ml") for value in stack.get(group) or []]
            tags = [str(value) for value in item.get("non_tech_tags") or []]
            technical.extend(tech)
            nontechnical.extend(tags)
            projects.append(ProfileItem(title=name, description=str(item.get("summary") or ""), skills=tech, link=item.get("repo_link")))
        profile = self.get_profile().model_copy(update={"projects": projects or self.get_profile().projects})
        self.save_profile(profile)
        job = JobRequirements(
            company_name=str(company.get("company_name") or ""), role=str(company.get("role") or ""),
            description=str(company.get("job_description") or company.get("company_description") or ""),
            required_skills=_unique(technical), keywords=_unique(nontechnical),
        )
        return self.create_document(job, "jvs", limit, source_latex)

    def get_document(self, document_id: str) -> ResumeDocument | None:
        return self.repository.get_document(document_id)

    def update_document(self, document: ResumeDocument, update: LatexUpdateRequest) -> ResumeDocument:
        changes = {field: getattr(update, field) for field in update.model_fields_set}
        changes["updated_at"] = datetime.now(timezone.utc).isoformat()
        updated = document.model_copy(update=changes)
        self.renderer.render(updated)
        return self.repository.save_document(updated)

    def latex(self, document: ResumeDocument) -> str:
        return self.renderer.render(document)

    def pdf(self, document: ResumeDocument) -> bytes:
        return self.compiler.compile(self.latex(document), self.output_dir / document.id)


def build_resume_builder_service() -> ResumeBuilderService:
    root = Path(os.getenv("RESUME_BUILDER_DIR", "data/resume_builder"))
    return ResumeBuilderService(JsonResumeBuilderRepository(root), PdfLatexCompiler(), root / "compiled")


def profile_from_pipeline_artifact(payload: dict) -> ProfessionalProfile:
    """Anti-corruption mapper between the existing parser artifact and builder domain."""
    links = payload.get("links") or {}
    return ProfessionalProfile(
        name=str(payload.get("candidate_name") or ""),
        summary=str(payload.get("summary") or ""),
        email=str((links.get("emails") or [""])[0]),
        phone=str((links.get("phones") or [""])[0]),
        links=[str(value) for value in (links.get("github"), links.get("linkedin"), links.get("portfolio")) if value],
        skills=[str(value) for value in payload.get("skills") or []],
        experiences=[ProfileItem(title=str(item.get("company_name") or "Experience"), date=str(item.get("date") or ""), description=str(item.get("description") or "")) for item in payload.get("experience") or []],
        projects=[ProfileItem(title=str(item.get("project_name") or "Project"), description=str(item.get("description") or ""), link=item.get("link")) for item in payload.get("projects") or []],
        education=[ProfileItem(title=str(item)) for item in payload.get("education") or []],
        certifications=[ProfileItem(title=str(item.get("name") or "Certification"), link=item.get("link")) for item in payload.get("certifications") or []],
        publications=[ProfileItem(title="Publication", description=str(item)) for item in payload.get("research") or []],
    )


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value.strip() for value in values if value.strip()))
