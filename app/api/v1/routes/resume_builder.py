from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.modules.resume_builder import ResumeBuilderService, build_resume_builder_service
from app.modules.resume_builder.model import (
    LatexUpdateRequest,
    ProfessionalProfile,
    PipelineTailorRequest,
    RecommendationRequest,
    ResumeDocumentRequest,
)
from app.modules.resume_builder.service import profile_from_pipeline_artifact

router = APIRouter(prefix="/resume-builder", tags=["resume-builder"])


@lru_cache(maxsize=1)
def get_service() -> ResumeBuilderService:
    return build_resume_builder_service()


@router.get("/profile")
def get_profile(service: ResumeBuilderService = Depends(get_service)) -> ProfessionalProfile:
    return service.get_profile()


@router.put("/profile")
def save_profile(profile: ProfessionalProfile, service: ResumeBuilderService = Depends(get_service)) -> ProfessionalProfile:
    return service.save_profile(profile)


@router.post("/profile/import-run/{run_id}")
def import_pipeline_profile(run_id: str, service: ResumeBuilderService = Depends(get_service)) -> ProfessionalProfile:
    from app.api.v1.services.run_store import get_run_store

    artifact = get_run_store().get_artifact(run_id, "resume")
    if not isinstance(artifact, dict):
        raise HTTPException(status_code=404, detail="Parsed resume artifact not found for this run.")
    return service.save_profile(profile_from_pipeline_artifact(artifact))


@router.post("/recommendations")
def recommend(payload: RecommendationRequest, service: ResumeBuilderService = Depends(get_service)):
    return service.recommend(payload.job, payload.limit)


@router.post("/documents")
def create_document(payload: ResumeDocumentRequest, service: ResumeBuilderService = Depends(get_service)):
    return service.create_document(payload.job, payload.template, payload.recommendation_limit, payload.source_latex)


@router.post("/documents/from-run/{run_id}")
def create_document_from_run(run_id: str, payload: PipelineTailorRequest, service: ResumeBuilderService = Depends(get_service)):
    from app.api.v1.services.run_store import get_run_store

    store = get_run_store()
    github = store.get_artifact(run_id, "github")
    matches_artifact = store.get_artifact(run_id, "matches")
    companies = store.get_companies(run_id)
    company = next((item for item in companies or [] if str(item.get("company_name")) == payload.company_name), None)
    if not isinstance(github, dict) or company is None or not isinstance(matches_artifact, (dict, list)):
        raise HTTPException(status_code=404, detail="GitHub, company, or match artifact is missing for this run.")
    matches = matches_artifact.get(payload.company_name, []) if isinstance(matches_artifact, dict) else matches_artifact
    return service.create_from_pipeline(
        source_latex=payload.source_latex, company=company, github=github,
        matches=matches if isinstance(matches, list) else [], limit=payload.recommendation_limit,
    )


@router.get("/documents/{document_id}")
def get_document(document_id: str, service: ResumeBuilderService = Depends(get_service)):
    return _document_or_404(service, document_id)


@router.put("/documents/{document_id}")
def update_document(document_id: str, payload: LatexUpdateRequest, service: ResumeBuilderService = Depends(get_service)):
    try:
        return service.update_document(_document_or_404(service, document_id), payload)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/documents/{document_id}/source")
def export_source(document_id: str, service: ResumeBuilderService = Depends(get_service)) -> Response:
    document = _document_or_404(service, document_id)
    source = service.latex(document)
    return Response(
        source,
        media_type="application/x-tex",
        headers={"Content-Disposition": f'attachment; filename="resume-{document_id}.tex"'},
    )


@router.get("/documents/{document_id}/pdf")
def export_pdf(document_id: str, service: ResumeBuilderService = Depends(get_service)) -> Response:
    document = _document_or_404(service, document_id)
    try:
        content = service.pdf(document)
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return Response(
        content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="resume-{document_id}.pdf"'},
    )


def _document_or_404(service: ResumeBuilderService, document_id: str):
    document = service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Resume document not found.")
    return document
