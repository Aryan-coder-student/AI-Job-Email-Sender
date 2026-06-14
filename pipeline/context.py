from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.modules.github.model import ParsedGitHubProfile
from app.modules.graph.serializers import (
    load_json_file,
    parsed_github_from_dict,
    parsed_resume_from_dict,
)
from app.modules.resume.model import ParsedResume
from pipeline.exceptions import PipelineConfigurationError


@dataclass
class PipelineContext:
    resume_path: Path | None = None
    companies_path: Path | None = None
    parsed_resume: ParsedResume | None = None
    parsed_github: ParsedGitHubProfile | None = None
    companies: list[dict[str, Any]] | None = None
    graph_result: dict[str, Any] | None = None
    candidate_id: str | None = None
    matches: list[dict[str, Any]] | None = None
    draft: dict[str, Any] | None = None
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
    def draft_path(self) -> Path:
        return self.output_dir / "draft.json"

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
        if from_step >= 3:
            self._load_parsed_resume()
            self._load_parsed_github()
            self._load_companies()
        if from_step >= 4:
            self._load_graph_result()
        if from_step >= 5:
            self._load_matches()

    def _load_parsed_resume(self) -> None:
        if self.parsed_resume is not None:
            return
        path = self.parsed_resume_path
        if not path.is_file():
            raise PipelineConfigurationError(f"Missing parsed resume artifact: {path}")
        self.parsed_resume = parsed_resume_from_dict(load_json_file(str(path)))

    def _load_parsed_github(self) -> None:
        if self.parsed_github is not None:
            return
        path = self.github_projects_path
        if not path.is_file():
            raise PipelineConfigurationError(f"Missing GitHub projects artifact: {path}")
        self.parsed_github = parsed_github_from_dict(load_json_file(str(path)))

    def _load_companies(self) -> None:
        if self.companies is not None:
            return
        if self.companies_path is None:
            raise PipelineConfigurationError("companies_path is required to load companies.")
        if not self.companies_path.is_file():
            raise PipelineConfigurationError(f"Missing companies artifact: {self.companies_path}")
        self.companies = load_json_file(str(self.companies_path))

    def _load_graph_result(self) -> None:
        if self.graph_result is not None:
            return
        path = self.graph_result_path
        if not path.is_file():
            raise PipelineConfigurationError(f"Missing graph build artifact: {path}")
        self.graph_result = load_json_file(str(path))
        self.candidate_id = self.graph_result["candidate"]["metadata"]["candidate_id"]

    def _load_matches(self) -> None:
        if self.matches is not None:
            return
        path = self.matches_path
        if not path.is_file():
            raise PipelineConfigurationError(f"Missing matches artifact: {path}")
        self.matches = load_json_file(str(path))


@dataclass(frozen=True)
class PipelineResult:
    context: PipelineContext
    steps_executed: tuple[int, ...]
