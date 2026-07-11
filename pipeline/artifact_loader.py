from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from app.modules.graph.serializers import (
    load_json_file,
    parsed_github_from_dict,
    parsed_resume_from_dict,
)
from pipeline.types import PipelineStep
from pipeline.validation import validate_artifact_exists

if TYPE_CHECKING:
    from pipeline.context import PipelineContext

T = TypeVar("T")


def _current_or_loaded(value: T | None, loader: Callable[[], T]) -> T:
    return value if value is not None else loader()


@dataclass(frozen=True)
class PipelineArtifactLoader:
    context: PipelineContext

    def load_required_state(self, *, from_step: int) -> None:
        if not self._should_load_required_state(from_step):
            return

        for loader in self._loaders_for(from_step):
            loader()

    def _should_load_required_state(self, from_step: int) -> bool:
        return from_step > min(PipelineStep)

    def _load_plan(self) -> tuple[tuple[int, tuple[Callable[[], None], ...]], ...]:
        return (
            (3, (self._load_parsed_resume, self._load_parsed_github)),
            (4, (self._load_graph_result,)),
            (5, (self._load_matches,)),
        )

    def _loaders_for(self, from_step: int) -> tuple[Callable[[], None], ...]:
        return tuple(
            loader
            for required_step, loaders in self._load_plan()
            for loader in loaders
            if from_step >= required_step
        )

    def _load_parsed_resume(self) -> None:
        self.context.parsed_resume = _current_or_loaded(
            self.context.parsed_resume,
            self._load_parsed_resume_artifact,
        )

    def _load_parsed_github(self) -> None:
        self.context.parsed_github = _current_or_loaded(
            self.context.parsed_github,
            self._load_parsed_github_artifact,
        )

    def _load_graph_result(self) -> None:
        self.context.graph_result = _current_or_loaded(
            self.context.graph_result,
            self._load_graph_result_artifact,
        )
        self.context.candidate_id = self.context.graph_result["candidate"]["metadata"][
            "candidate_id"
        ]

    def _load_matches(self) -> None:
        self.context.matches = _current_or_loaded(
            self.context.matches,
            self._load_matches_artifact,
        )

    def _load_parsed_resume_artifact(self) -> Any:
        payload = self._read_artifact(self.context.parsed_resume_path, "parsed resume")
        return parsed_resume_from_dict(payload)

    def _load_parsed_github_artifact(self) -> Any:
        payload = self._read_artifact(self.context.github_projects_path, "GitHub projects")
        return parsed_github_from_dict(payload)

    def _load_graph_result_artifact(self) -> Any:
        return self._read_artifact(self.context.graph_result_path, "graph build")

    def _load_matches_artifact(self) -> Any:
        return self._read_artifact(self.context.matches_path, "matches")

    def _read_artifact(self, path: Path, name: str) -> Any:
        return load_json_file(str(validate_artifact_exists(path, name)))
