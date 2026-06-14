from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pipeline.types import PipelineStep


@dataclass(frozen=True)
class PipelineOptions:
    target_company: str = "10up"
    recipient_email: str | None = None
    from_step: int = 1
    dry_run: bool = False
    no_enqueue: bool = False
    skip_enrichment: bool = False
    skip_services: bool = False
    clear_graph: bool = False
    max_repos: int = 100
    max_companies: int = 25
    max_github_enrichment: int = 10
    mail_limit: int = 10
    top_matches: int = 5
    job_url: str | None = None
    output_dir: Path = field(default_factory=lambda: Path("data"))
    steps: tuple[PipelineStep, ...] | None = None

    def resolved_steps(self) -> tuple[PipelineStep, ...]:
        if self.steps is not None:
            return self.steps
        return tuple(step for step in PipelineStep if step.value >= self.from_step)
