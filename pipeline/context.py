from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.modules.github.model import ParsedGitHubProfile
from app.modules.resume.model import ParsedResume
from pipeline.artifact_loader import PipelineArtifactLoader


@dataclass
class PipelineContext:
    resume_path: Path | None = None
    companies_path: Path | None = None
    parsed_resume: ParsedResume | None = None
    parsed_github: ParsedGitHubProfile | None = None
    companies: list[dict[str, Any]] | None = None
    graph_result: dict[str, Any] | None = None
    candidate_id: str | None = None
    matches: dict[str, list[dict[str, Any]]] | None = None
    drafts: dict[str, dict[str, Any]] | None = None
    mail_results: list[dict[str, Any]] | None = None
    output_dir: Path = field(default_factory=lambda: Path("data"))

    @property
    def parsed_resume_path(self) -> Path:
        return self.output_dir / "parse_resume.json"

    @property
    def github_projects_path(self) -> Path:
        return self.output_dir / "github_projects_resume.json"

    @property
    def graph_result_path(self) -> Path:
        return self.output_dir / "graph_build.json"

    @property
    def matches_path(self) -> Path:
        return self.output_dir / "matches.json"

    @property
    def drafts_path(self) -> Path:
        return self.output_dir / "drafts.json"

    @property
    def mail_result_path(self) -> Path:
        return self.output_dir / "mail_queue_result.json"

    def ensure_output_dir(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_json(self, path: Path, payload: Any) -> None:
        self.ensure_output_dir()
        path.write_text(
            f"{json.dumps(payload, indent=2, ensure_ascii=False)}\n",
            encoding="utf-8",
        )

    def load_artifact_state(self, *, from_step: int) -> None:
        PipelineArtifactLoader(self).load_required_state(from_step=from_step)


@dataclass(frozen=True)
class PipelineResult:
    context: PipelineContext
    steps_executed: tuple[int, ...]
