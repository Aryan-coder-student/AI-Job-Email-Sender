from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.v1.errors import not_found
from app.api.v1.schemas.runs import DraftUpdateRequest, ProcessMailRequest, ResumeRunRequest
from app.api.v1.services.run_store import get_run_store
from app.core.exceptions import InvalidExcelError
from app.modules.company_imports import preview_company_import

router = APIRouter(prefix="/runs", tags=["pipeline"])


@router.get("")
def list_pipeline_runs() -> list[dict[str, Any]]:
    return get_run_store().list_runs()


@router.post("/companies/preview")
async def preview_pipeline_companies(companies: UploadFile = File(...)) -> dict[str, Any]:
    try:
        return preview_company_import(
            content=await companies.read(),
            filename=companies.filename or "companies",
            output_dir=get_run_store().output_dir,
        )
    except (InvalidExcelError, UnicodeDecodeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("")
async def create_pipeline_run(
    background_tasks: BackgroundTasks,
    resume: UploadFile | None = File(default=None),
    companies: UploadFile | None = File(default=None),
    target_company: str = Form(default=""),
    selected_companies: str = Form(default="[]"),
    recipient_email: str | None = Form(default=None),
    job_url: str | None = Form(default=None),
    max_repos: int = Form(default=100),
    max_companies: int = Form(default=25),
    top_matches: int = Form(default=5),
    dry_run: bool = Form(default=True),
    no_enqueue: bool = Form(default=False),
    skip_enrichment: bool = Form(default=False),
    skip_services: bool = Form(default=False),
    clear_graph: bool = Form(default=False),
) -> dict[str, Any]:
    store = get_run_store()
    companies_content = await companies.read() if companies else None
    run = store.create_run(
        config={
            "target_company": target_company,
            "recipient_email": recipient_email,
            "job_url": job_url,
            "max_repos": max_repos,
            "max_companies": max_companies,
            "top_matches": top_matches,
            "dry_run": dry_run,
            "no_enqueue": no_enqueue,
            "skip_enrichment": skip_enrichment,
            "skip_services": skip_services,
            "clear_graph": clear_graph,
        },
        resume_filename=resume.filename if resume else None,
        companies_filename=companies.filename if companies else None,
        resume_content=await resume.read() if resume else None,
        selected_companies=_selected_companies(
            payload=selected_companies,
            content=companies_content,
            filename=companies.filename if companies else "companies",
        ),
    )
    background_tasks.add_task(store.execute_run, run["run_id"])
    return run


@router.get("/{run_id}")
def get_pipeline_run(run_id: str) -> dict[str, Any]:
    run = get_run_store().get_run(run_id)
    if run is None:
        raise not_found("Run not found.")

    return run


@router.get("/{run_id}/events")
def stream_pipeline_run_events(run_id: str) -> StreamingResponse:
    run = get_run_store().get_run(run_id)
    if run is None:
        raise not_found("Run not found.")

    return StreamingResponse(_run_event_stream(run), media_type="text/event-stream")


@router.post("/{run_id}/retry")
def retry_pipeline_run(run_id: str, background_tasks: BackgroundTasks) -> dict[str, Any]:
    store = get_run_store()
    run = store.retry_run(run_id)
    if run is None:
        raise not_found("Run not found.")

    background_tasks.add_task(store.execute_run, run_id)
    return run


@router.post("/{run_id}/resume")
def resume_pipeline_run(
    run_id: str,
    payload: ResumeRunRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    store = get_run_store()
    run = store.resume_run(run_id, from_step=payload.from_step)
    if run is None:
        raise not_found("Run not found.")

    background_tasks.add_task(store.execute_run, run_id)
    return run


@router.get("/{run_id}/companies")
def get_pipeline_companies(run_id: str) -> list[dict[str, Any]]:
    companies = get_run_store().get_companies(run_id)
    if companies is None:
        raise not_found("Run not found.")

    return companies


@router.get("/{run_id}/artifacts/{artifact_type}")
def get_pipeline_artifact(run_id: str, artifact_type: str) -> Any:
    artifact = get_run_store().get_artifact(run_id, artifact_type)
    if artifact is None:
        raise not_found("Artifact not found.")

    return artifact


@router.put("/{run_id}/draft")
def update_pipeline_draft(run_id: str, payload: DraftUpdateRequest) -> dict[str, Any]:
    draft = get_run_store().update_draft(run_id, payload.model_dump(exclude_unset=True))
    if draft is None:
        raise not_found("Run or draft not found.")

    return draft


@router.post("/{run_id}/draft/enqueue")
def enqueue_pipeline_draft(run_id: str) -> dict[str, Any]:
    draft = get_run_store().enqueue_draft(run_id)
    if draft is None:
        raise not_found("Run or draft not found.")

    return draft


@router.post("/{run_id}/mail/process")
def process_pipeline_mail(run_id: str, payload: ProcessMailRequest) -> list[dict[str, Any]]:
    result = get_run_store().process_mail(
        run_id,
        dry_run=payload.dry_run,
        limit=payload.limit,
    )
    if result is None:
        raise not_found("Run not found.")

    return result


async def _run_event_stream(run: dict[str, Any]) -> Any:
    yield f"event: snapshot\ndata: {json.dumps(run)}\n\n"
    await asyncio.sleep(0.1)
    yield "event: heartbeat\ndata: {}\n\n"


def _selected_companies(
    *,
    payload: str,
    content: bytes | None,
    filename: str | None,
) -> list[dict[str, Any]]:
    selected = _parse_selected_companies(payload)
    if selected or not content:
        return selected

    return _parse_company_upload(content=content, filename=filename or "companies")


def _parse_selected_companies(payload: str) -> list[dict[str, Any]]:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=400, detail="Selected companies must be valid JSON.") from error

    if not isinstance(value, list):
        raise HTTPException(status_code=400, detail="Selected companies must be a list.")

    return [item for item in value if isinstance(item, dict)]


def _parse_company_upload(*, content: bytes, filename: str) -> list[dict[str, Any]]:
    try:
        preview = preview_company_import(
            content=content,
            filename=filename,
            output_dir=get_run_store().output_dir,
        )
    except (InvalidExcelError, UnicodeDecodeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return [
        row["normalized"]
        for row in preview["rows"]
        if row.get("is_valid") and isinstance(row.get("normalized"), dict)
    ]
