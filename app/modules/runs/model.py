from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

PipelineRunStatus = Literal["created", "running", "completed", "failed"]
PipelineStepState = Literal["pending", "running", "completed", "failed", "skipped"]

ARTIFACT_FILES: dict[str, str] = {
    "resume": "parse_resume.json",
    "github": "github_projects_resume.json",
    "graph": "graph_build.json",
    "matches": "matches.json",
    "drafts": "drafts.json",
    "mail": "mail_queue_result.json",
}

PIPELINE_STEPS = (
    ("parse_resume", "Parse Resume", "resume"),
    ("parse_github", "Parse GitHub", "github"),
    ("build_graph", "Build Graph + Vectors", "graph"),
    ("rank_projects", "Rank Projects", "matches"),
    ("generate_draft", "Generate Draft", "drafts"),
    ("process_mail_queue", "Process Mail Queue", "mail"),
)


@dataclass
class PipelineStepRecord:
    key: str
    label: str
    status: PipelineStepState = "pending"
    artifact_type: str | None = None
    artifact_path: str | None = None
    summary: str | None = None
    error: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PipelineStepRecord:
        return cls(
            key=str(payload["key"]),
            label=str(payload["label"]),
            status=payload.get("status", "pending"),
            artifact_type=payload.get("artifact_type"),
            artifact_path=payload.get("artifact_path"),
            summary=payload.get("summary"),
            error=payload.get("error"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "status": self.status,
            "artifact_type": self.artifact_type,
            "artifact_path": self.artifact_path,
            "summary": self.summary,
            "error": self.error,
        }


@dataclass
class PipelineRunRecord:
    run_id: str
    status: PipelineRunStatus
    created_at: str
    updated_at: str
    config: dict[str, Any]
    steps: list[PipelineStepRecord]
    latest_error: str | None = None
    logs: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PipelineRunRecord:
        return cls(
            run_id=str(payload["run_id"]),
            status=payload.get("status", "created"),
            created_at=str(payload["created_at"]),
            updated_at=str(payload["updated_at"]),
            config=dict(payload.get("config") or {}),
            steps=_steps_from_payload(payload),
            latest_error=payload.get("latest_error"),
            logs=list(payload.get("logs") or []),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "config": self.config,
            "steps": [step.to_dict() for step in self.steps],
            "latest_error": self.latest_error,
            "logs": self.logs,
        }


def new_pipeline_steps() -> list[PipelineStepRecord]:
    return [
        PipelineStepRecord(key=key, label=label, artifact_type=artifact_type)
        for key, label, artifact_type in PIPELINE_STEPS
    ]


def artifact_type_for_step(key: str) -> str | None:
    for step_key, _, artifact_type in PIPELINE_STEPS:
        if step_key == key:
            return artifact_type
    return None


def _steps_from_payload(payload: dict[str, Any]) -> list[PipelineStepRecord]:
    return [
        PipelineStepRecord.from_dict(step)
        for step in payload.get("steps", [])
        if isinstance(step, dict)
    ]
