from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from app.modules.runs.model import (
    ARTIFACT_FILES,
    PIPELINE_STEPS,
    PipelineRunRecord,
    PipelineRunStatus,
    PipelineStepRecord,
    artifact_type_for_step,
    new_pipeline_steps,
)
from app.modules.runs.repository import JsonRunRepository, path_from_config
from pipeline.executor import PipelineExecutionRequest, PipelineExecutionService
from pipeline.types import PipelineStep


class PipelineRunStore:
    def __init__(
        self,
        *,
        output_dir: Path | str = "data",
        executor: PipelineExecutionService | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self._repository = JsonRunRepository(output_dir=self.output_dir)
        self._executor = executor or PipelineExecutionService()
        self._lock = Lock()
        self._runs = self._repository.load_runs()
        self._seed_demo_run()

    def list_runs(self) -> list[dict[str, Any]]:
        with self._lock:
            runs = sorted(self._runs.values(), key=lambda run: run.created_at, reverse=True)
            return [run.to_dict() for run in runs]

    def create_run(
        self,
        *,
        config: dict[str, Any],
        resume_filename: str | None = None,
        companies_filename: str | None = None,
        resume_content: bytes | None = None,
        selected_companies: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        run = self._build_run(
            config=config,
            resume_filename=resume_filename,
            companies_filename=companies_filename,
            resume_content=resume_content,
            selected_companies=selected_companies or [],
        )
        self._save_run(run)
        return run.to_dict()

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._lock:
            run = self._runs.get(run_id)
            return run.to_dict() if run else None

    def retry_run(self, run_id: str) -> dict[str, Any] | None:
        return self._reset_run(run_id, log="Retry requested from frontend.")

    def resume_run(self, run_id: str, *, from_step: str | None = None) -> dict[str, Any] | None:
        step_label = from_step or "current"
        return self._reset_run(run_id, log=f"Resume requested from step: {step_label}.")

    def execute_run(self, run_id: str) -> None:
        run = self._get_record(run_id)
        if run is None:
            return

        try:
            request = _pipeline_execution_request(run)
        except ValueError as error:
            self.mark_run_failed(run_id, str(error))
            return

        self._executor.execute(
            request=request,
            observer=_RunPipelineObserver(store=self, run_id=run_id),
        )

    def update_draft(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        if self.get_run(run_id) is None:
            return None

        drafts = self.get_artifact(run_id, "drafts") or {}
        editable = {key: value for key, value in payload.items() if key in _DRAFT_EDIT_FIELDS}
        company_name = payload.get("company_name")
        
        if company_name and company_name in drafts:
            drafts[company_name] = {**drafts[company_name], **editable, "status": "draft"}
        else:
            # Apply edits to all drafts
            for name in drafts:
                drafts[name] = {**drafts[name], **editable, "status": "draft"}
        
        artifact_path = self._artifact_path(run_id, "drafts")
        if artifact_path:
            artifact_path.write_text(json.dumps(drafts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        
        return drafts

    def enqueue_draft(self, run_id: str) -> dict[str, Any] | None:
        drafts = self.get_artifact(run_id, "drafts")
        if drafts is None:
            return None
        for company_name in drafts:
            drafts[company_name]["status"] = "queued"
        
        artifact_path = self._artifact_path(run_id, "drafts")
        if artifact_path:
            artifact_path.write_text(json.dumps(drafts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        
        return drafts

    def process_mail(self, run_id: str, *, dry_run: bool, limit: int) -> list[dict[str, Any]] | None:
        if self.get_run(run_id) is None:
            return None

        mail_result = self.get_artifact(run_id, "mail")
        if isinstance(mail_result, list) and mail_result:
            return mail_result[:limit]

        draft = self.get_artifact(run_id, "drafts") or {}
        return [_fallback_mail_result(run_id=run_id, draft=draft, dry_run=dry_run)]

    def get_companies(self, run_id: str) -> list[dict[str, Any]] | None:
        run = self._get_record(run_id)
        if run is None:
            return None

        companies_path = path_from_config(run.config, "companies_path")
        if companies_path and companies_path.is_file():
            payload = json.loads(companies_path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, list) else []

        return self._demo_companies(run_id) or list(run.config.get("selected_companies") or [])

    def get_artifact(self, run_id: str, artifact_type: str) -> Any | None:
        artifact_path = self._artifact_path(run_id, artifact_type)
        if not artifact_path or not artifact_path.is_file():
            return None

        return json.loads(artifact_path.read_text(encoding="utf-8"))

    def mark_run_running(self, run_id: str) -> None:
        self._update_run(run_id, status="running", log="Pipeline orchestration started.")

    def mark_run_completed(self, run_id: str) -> None:
        self._update_run(run_id, status="completed", log="Pipeline orchestration completed.")

    def mark_run_failed(self, run_id: str, error: str) -> None:
        self._update_run(
            run_id,
            status="failed",
            latest_error=error,
            log=f"Pipeline orchestration failed: {error}",
        )

    def mark_step_running(self, run_id: str, key: str) -> None:
        self._update_step(run_id, key, status="running", error=None)

    def mark_step_completed(self, run_id: str, key: str) -> None:
        artifact_type = artifact_type_for_step(key)
        artifact_path = self._artifact_path(run_id, artifact_type)
        self._update_step(
            run_id,
            key,
            status="completed",
            artifact_path=str(artifact_path) if artifact_path and artifact_path.is_file() else None,
            summary=_artifact_summary(artifact_type, artifact_path),
            error=None,
        )

    def _build_run(
        self,
        *,
        config: dict[str, Any],
        resume_filename: str | None,
        companies_filename: str | None,
        resume_content: bytes | None,
        selected_companies: list[dict[str, Any]],
    ) -> PipelineRunRecord:
        run_id = uuid.uuid4().hex
        resume_path = self._repository.write_resume_upload(
            run_id=run_id,
            filename=resume_filename,
            content=resume_content,
        )
        companies_path = self._repository.write_companies(
            run_id=run_id,
            companies=selected_companies,
        )
        return _new_run_record(
            run_id=run_id,
            config=_run_config(
                config=config,
                resume_filename=resume_filename,
                companies_filename=companies_filename,
                resume_path=resume_path,
                companies_path=companies_path,
                output_dir=self._repository.artifact_dir(run_id),
                selected_companies=selected_companies,
            ),
        )

    def _save_run(self, run: PipelineRunRecord) -> None:
        with self._lock:
            self._runs[run.run_id] = run
            self._repository.save_runs(self._runs)

    def _reset_run(self, run_id: str, *, log: str) -> dict[str, Any] | None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return None

            run.status = "running"
            run.updated_at = _utc_now()
            run.latest_error = None
            run.logs.append(log)
            for step in run.steps:
                step.status = "pending"
                step.error = None
            self._repository.save_runs(self._runs)
            return run.to_dict()

    def _update_run(
        self,
        run_id: str,
        *,
        status: PipelineRunStatus,
        latest_error: str | None = None,
        log: str | None = None,
    ) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return

            run.status = status
            run.updated_at = _utc_now()
            run.latest_error = latest_error
            if log:
                run.logs.append(log)
            self._repository.save_runs(self._runs)

    def _update_step(self, run_id: str, key: str, **updates: Any) -> None:
        with self._lock:
            step = self._find_step(run_id, key)
            if step is None:
                return

            for field_name, value in updates.items():
                setattr(step, field_name, value)
            self._runs[run_id].updated_at = _utc_now()
            self._repository.save_runs(self._runs)

    def _find_step(self, run_id: str, key: str) -> PipelineStepRecord | None:
        run = self._runs.get(run_id)
        if run is None:
            return None

        return next((step for step in run.steps if step.key == key), None)

    def _artifact_path(self, run_id: str, artifact_type: str | None) -> Path | None:
        if artifact_type is None or artifact_type not in ARTIFACT_FILES:
            return None

        run = self._get_record(run_id)
        if run is None:
            return None

        return self._repository.artifact_path(run=run, artifact_type=artifact_type) or (
            self.output_dir / ARTIFACT_FILES[artifact_type]
        )

    def _get_record(self, run_id: str) -> PipelineRunRecord | None:
        with self._lock:
            return self._runs.get(run_id)

    def _seed_demo_run(self) -> None:
        if "local-demo" in self._runs:
            return

        artifacts = _available_demo_artifacts(self.output_dir)
        if not artifacts:
            return

        self._runs["local-demo"] = _demo_run(artifacts)

    def _demo_companies(self, run_id: str) -> list[dict[str, Any]] | None:
        demo_path = self.output_dir / "companies_sheet.json"
        if run_id != "local-demo" or not demo_path.is_file():
            return None

        payload = json.loads(demo_path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, list) else []


class _RunPipelineObserver:
    def __init__(self, *, store: PipelineRunStore, run_id: str) -> None:
        self._store = store
        self._run_id = run_id

    def pipeline_started(self) -> None:
        self._store.mark_run_running(self._run_id)

    def pipeline_completed(self) -> None:
        self._store.mark_run_completed(self._run_id)

    def pipeline_failed(self, error: str) -> None:
        self._store.mark_run_failed(self._run_id, error)

    def step_started(self, step: PipelineStep) -> None:
        self._store.mark_step_running(self._run_id, _step_key(step))

    def step_completed(self, step: PipelineStep) -> None:
        self._store.mark_step_completed(self._run_id, _step_key(step))


_DRAFT_EDIT_FIELDS = {"to", "subject", "body_text", "body_html"}


def _new_run_record(*, run_id: str, config: dict[str, Any]) -> PipelineRunRecord:
    now = _utc_now()
    return PipelineRunRecord(
        run_id=run_id,
        status="created",
        created_at=now,
        updated_at=now,
        config=config,
        steps=new_pipeline_steps(),
        logs=[
            "Run created from frontend API.",
            f"Selected {config['selected_company_count']} company row(s).",
        ],
    )


def _run_config(
    *,
    config: dict[str, Any],
    resume_filename: str | None,
    companies_filename: str | None,
    resume_path: Path | None,
    companies_path: Path,
    output_dir: Path,
    selected_companies: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        **config,
        "target_company": _resolve_target_company(config, selected_companies),
        "resume_filename": resume_filename,
        "companies_filename": companies_filename,
        "resume_path": str(resume_path) if resume_path else None,
        "companies_path": str(companies_path),
        "output_dir": str(output_dir),
        "selected_companies": selected_companies,
        "selected_company_count": len(selected_companies),
    }


def _resolve_target_company(config: dict[str, Any], companies: list[dict[str, Any]]) -> str:
    configured = str(config.get("target_company") or "").strip()
    if configured:
        return configured

    for company in companies:
        company_name = str(company.get("company_name") or "").strip()
        if company_name:
            return company_name

    return ""


def _pipeline_execution_request(run: PipelineRunRecord) -> PipelineExecutionRequest:
    output_dir = _required_path(run, "output_dir", "Run output directory", must_be_file=False)
    return PipelineExecutionRequest(
        resume_path=_required_path(run, "resume_path", "Resume file"),
        companies_path=_required_path(run, "companies_path", "Selected companies file"),
        output_dir=output_dir,
        target_company=str(run.config.get("target_company") or ""),
        recipient_email=_optional_str(run.config.get("recipient_email")),
        dry_run=bool(run.config.get("dry_run", True)),
        no_enqueue=bool(run.config.get("no_enqueue", False)),
        skip_enrichment=bool(run.config.get("skip_enrichment", False)),
        skip_services=bool(run.config.get("skip_services", False)),
        clear_graph=bool(run.config.get("clear_graph", False)),
        max_repos=int(run.config.get("max_repos") or 100),
        max_companies=int(run.config.get("max_companies") or 25),
        top_matches=int(run.config.get("top_matches") or 5),
        job_url=_optional_str(run.config.get("job_url")),
    )


def _required_path(
    run: PipelineRunRecord,
    key: str,
    label: str,
    *,
    must_be_file: bool = True,
) -> Path:
    path = path_from_config(run.config, key)
    if path is None or (must_be_file and not path.is_file()):
        raise ValueError(f"{label} is required before launching orchestration.")
    return path


def _optional_str(value: object) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _step_key(step: PipelineStep) -> str:
    return {
        PipelineStep.PARSE_RESUME: "parse_resume",
        PipelineStep.PARSE_GITHUB: "parse_github",
        PipelineStep.BUILD_GRAPH: "build_graph",
        PipelineStep.RANK_PROJECTS: "rank_projects",
        PipelineStep.GENERATE_DRAFT: "generate_draft",
        PipelineStep.PROCESS_MAIL_QUEUE: "process_mail_queue",
    }[step]


def _fallback_mail_result(
    *,
    run_id: str,
    draft: dict[str, Any],
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "draft_id": draft.get("draft_id") or run_id,
        "to": draft.get("to"),
        "status": "dry_run" if dry_run else "queued",
    }


def _artifact_summary(artifact_type: str | None, artifact_path: Path | None) -> str | None:
    if not artifact_type or not artifact_path or not artifact_path.is_file():
        return None

    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None

    return _summarize_artifact(artifact_type, payload)


def _summarize_artifact(artifact_type: str, payload: Any) -> str | None:
    if artifact_type == "resume":
        return str(payload.get("candidate_name") or payload.get("filename") or "Parsed resume")
    if artifact_type == "github":
        return f"{len(payload.get('projects') or [])} GitHub projects"
    if artifact_type == "matches" and isinstance(payload, dict):
        return f"{len(payload)} companies ranked"
    if artifact_type == "drafts":
        if isinstance(payload, dict):
            return f"{len(payload)} email drafts generated"
        return str(payload.get("subject") or "Generated draft")
    if artifact_type == "mail" and isinstance(payload, list):
        return f"{len(payload)} mail results"
    if artifact_type == "graph":
        return "Graph build artifact"
    return None


def _available_demo_artifacts(output_dir: Path) -> dict[str, Path]:
    return {
        artifact_type: output_dir / filename
        for artifact_type, filename in ARTIFACT_FILES.items()
        if (output_dir / filename).is_file()
    }


def _demo_run(artifacts: dict[str, Path]) -> PipelineRunRecord:
    now = _utc_now()
    return PipelineRunRecord(
        run_id="local-demo",
        status="completed",
        created_at=now,
        updated_at=now,
        config={"target_company": "10up", "dry_run": True, "source": "data artifacts"},
        steps=_demo_steps(artifacts),
        logs=["Loaded existing data artifacts as a demo run."],
    )


def _demo_steps(artifacts: dict[str, Path]) -> list[PipelineStepRecord]:
    steps: list[PipelineStepRecord] = []
    for key, label, artifact_type in PIPELINE_STEPS:
        artifact_path = artifacts.get(artifact_type)
        steps.append(
            PipelineStepRecord(
                key=key,
                label=label,
                status="completed" if artifact_path else "pending",
                artifact_type=artifact_type,
                artifact_path=str(artifact_path) if artifact_path else None,
                summary=_artifact_summary(artifact_type, artifact_path),
            )
        )
    return steps


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
