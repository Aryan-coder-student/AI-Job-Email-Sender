from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pipeline.application import ApplicationPipeline
from pipeline.builder import ApplicationPipelineBuilder
from pipeline.config import PipelineOptions
from pipeline.types import ALL_PIPELINE_STEPS, PipelineStep


@dataclass(frozen=True)
class PipelineExecutionRequest:
    resume_path: Path
    companies_path: Path
    output_dir: Path
    target_company: str
    recipient_email: str | None = None
    dry_run: bool = True
    no_enqueue: bool = False
    skip_enrichment: bool = False
    skip_services: bool = False
    clear_graph: bool = False
    max_repos: int = 100
    max_companies: int = 25
    top_matches: int = 5
    job_url: str | None = None
    steps: tuple[PipelineStep, ...] = ALL_PIPELINE_STEPS


class PipelineExecutionObserver(Protocol):
    def pipeline_started(self) -> None: ...

    def pipeline_completed(self) -> None: ...

    def pipeline_failed(self, error: str) -> None: ...

    def step_started(self, step: PipelineStep) -> None: ...

    def step_completed(self, step: PipelineStep) -> None: ...


class PipelineExecutionService:
    def execute(
        self,
        *,
        request: PipelineExecutionRequest,
        observer: PipelineExecutionObserver,
    ) -> None:
        try:
            observer.pipeline_started()
            pipeline = _build_pipeline(request)
            pipeline.run(steps=request.steps, observer=observer)
            observer.pipeline_completed()
        except Exception as error:
            observer.pipeline_failed(str(error))


def _build_pipeline(request: PipelineExecutionRequest) -> ApplicationPipeline:
    return (
        ApplicationPipelineBuilder(project_root=Path("."))
        .with_resume(request.resume_path)
        .with_companies(request.companies_path)
        .with_options(_options_from_request(request))
        .build()
    )


def _options_from_request(request: PipelineExecutionRequest) -> PipelineOptions:
    return PipelineOptions(
        target_company=request.target_company,
        recipient_email=request.recipient_email,
        dry_run=request.dry_run,
        no_enqueue=request.no_enqueue,
        skip_enrichment=request.skip_enrichment,
        skip_services=request.skip_services,
        clear_graph=request.clear_graph,
        max_repos=request.max_repos,
        max_companies=request.max_companies,
        top_matches=request.top_matches,
        job_url=request.job_url,
        output_dir=request.output_dir,
    )
