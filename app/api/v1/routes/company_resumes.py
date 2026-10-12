"""Run-scoped company resume artifacts and editing endpoints."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.api.v1.services.run_store import get_run_store
from app.modules.resume_builder.company_batch import CompanyResumeBatch
from app.modules.resume_builder.model import LatexUpdateRequest

router = APIRouter(prefix="/resume-builder/runs", tags=["company-resumes"])


def _batch(run_id: str) -> CompanyResumeBatch:
    run = get_run_store().get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Pipeline run not found.")
    output = run["config"].get("output_dir")
    if not output:
        raise HTTPException(status_code=404, detail="Run has no output directory.")
    return CompanyResumeBatch(Path(output))


def _document(run_id: str, key: str):
    batch = _batch(run_id)
    entry = batch.get_entry(key)
    if entry is None:
        raise HTTPException(status_code=404, detail="Company resume not found.")
    document = batch.service.get_document(entry["document_id"])
    if document is None:
        raise HTTPException(status_code=404, detail="Company resume document not found.")
    return batch, entry, document


@router.get("/{run_id}/companies")
def list_company_resumes(run_id: str):
    return _batch(run_id).read_manifest()


@router.post("/{run_id}/companies/generate")
def generate_company_resumes(run_id: str):
    store = get_run_store()
    batch = _batch(run_id)
    resume = store.get_artifact(run_id, "resume")
    github = store.get_artifact(run_id, "github")
    matches = store.get_artifact(run_id, "matches")
    companies = store.get_companies(run_id)
    if not isinstance(resume, dict) or not isinstance(github, dict) or not isinstance(matches, dict) or companies is None:
        raise HTTPException(status_code=409, detail="Complete resume, GitHub, companies, and matching artifacts first.")
    try:
        return batch.generate(resume=resume, github=github, companies=companies, matches=matches)
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/{run_id}/companies/{company_key}")
def get_company_resume(run_id: str, company_key: str):
    return _document(run_id, company_key)[2]


@router.put("/{run_id}/companies/{company_key}")
def update_company_resume(run_id: str, company_key: str, payload: LatexUpdateRequest):
    batch, _, document = _document(run_id, company_key)
    try:
        updated = batch.service.update_document(document, payload)
        batch.service.pdf(updated)
    except (ValueError, RuntimeError) as error:
        # A LaTeX source that fails compilation must not replace a valid resume.
        batch.service.repository.save_document(document)
        raise HTTPException(status_code=422, detail=str(error)) from error
    return updated


@router.get("/{run_id}/companies/{company_key}/source")
def export_company_source(run_id: str, company_key: str):
    batch, entry, document = _document(run_id, company_key)
    return Response(
        batch.service.latex(document),
        media_type="application/x-tex",
        headers={"Content-Disposition": f'attachment; filename="resume-{entry["company_key"]}.tex"'},
    )


@router.get("/{run_id}/companies/{company_key}/pdf")
def export_company_pdf(run_id: str, company_key: str):
    batch, entry, document = _document(run_id, company_key)
    try:
        content = batch.service.pdf(document)
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return Response(
        content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="resume-{entry["company_key"]}.pdf"'},
    )
