"""Generate a separate, immutable candidate resume for each company with ranked matches.

Artifacts live inside a single pipeline run directory. No global candidate profile
is overwritten, and no resume is sent to any recipient automatically.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from app.modules.llm.factory import build_default_llm_router
from app.modules.resume_builder.latex import PdfLatexCompiler
from app.modules.resume_builder.llm_tailoring import CompanyResumeTailor
from app.modules.resume_builder.model import JobRequirements
from app.modules.resume_builder.repository import JsonResumeBuilderRepository
from app.modules.resume_builder.service import ResumeBuilderService, profile_from_pipeline_artifact


def company_key(company_name: str) -> str:
    """An opaque, filesystem-safe company identifier within a run."""
    return hashlib.sha256(company_name.strip().casefold().encode("utf-8")).hexdigest()[:20]


class CompanyResumeBatch:
    def __init__(self, output_dir: Path, compiler=None, llm_router=None) -> None:
        self.output_dir = Path(output_dir)
        self.root = self.output_dir / "company_resumes"
        self._llm_router = llm_router
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
        # Intentionally no regex/keyword overlap fallback: generation requires an
        # available LLM provider and fails explicitly if the model is unavailable.
        eligible_companies = [
            company for company in companies
            if str(company.get("company_name") or "").strip()
            and matches.get(str(company.get("company_name") or "").strip())
        ]
        if not eligible_companies:
            raise ValueError("No companies have ranked project matches.")
        tailor = CompanyResumeTailor(self._llm_router or build_default_llm_router())
        entries: dict[str, dict[str, Any]] = {}
        for company in eligible_companies:
            name = str(company["company_name"]).strip()
            ranked = matches[name]
            if name in entries:
                raise ValueError(f"Duplicate company name in resume batch: {name}")
            result = tailor.tailor(
                profile=original_profile,
                company=company,
                github=github,
                matches=ranked,
                limit=limit,
            )
            job = JobRequirements(
                company_name=name,
                role=str(company.get("role") or ""),
                description=str(company.get("job_description") or company.get("company_description") or ""),
            )
            document = self.service.create_llm_curated_document(
                job,
                profile=result.profile,
                recommendations=result.recommendations,
                selected_skills=result.selected_skills,
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
                "llm_provider": result.provider,
                "llm_model": result.model,
                "status": "ready",
            }

        self.output_dir.mkdir(parents=True, exist_ok=True)
        pending = self.manifest_path.with_suffix(".json.tmp")
        pending.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        pending.replace(self.manifest_path)
        return entries
