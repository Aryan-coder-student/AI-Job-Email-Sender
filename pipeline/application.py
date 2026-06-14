from __future__ import annotations

from pathlib import Path
from typing import Mapping

from pipeline.config import PipelineOptions
from pipeline.context import PipelineContext, PipelineResult
from pipeline.exceptions import PipelineConfigurationError, PipelineStepError
from pipeline.steps.base import StepHandler
from pipeline.steps.handlers import (
    BuildGraphStep,
    GenerateDraftStep,
    ParseGitHubStep,
    ParseResumeStep,
    ProcessMailQueueStep,
    RankProjectsStep,
    ensure_services_ready,
)
from pipeline.types import PipelineStep


DEFAULT_STEP_HANDLERS: Mapping[PipelineStep, StepHandler] = {
    PipelineStep.PARSE_RESUME: ParseResumeStep(),
    PipelineStep.PARSE_GITHUB: ParseGitHubStep(),
    PipelineStep.BUILD_GRAPH: BuildGraphStep(),
    PipelineStep.RANK_PROJECTS: RankProjectsStep(),
    PipelineStep.GENERATE_DRAFT: GenerateDraftStep(),
    PipelineStep.PROCESS_MAIL_QUEUE: ProcessMailQueueStep(),
}


class ApplicationPipeline:
    def __init__(
        self,
        *,
        context: PipelineContext,
        options: PipelineOptions,
        project_root: Path,
        step_handlers: Mapping[PipelineStep, StepHandler] | None = None,
    ) -> None:
        self._context = context
        self._options = options
        self._project_root = project_root
        self._step_handlers = step_handlers or DEFAULT_STEP_HANDLERS

    @property
    def context(self) -> PipelineContext:
        return self._context

    @property
    def options(self) -> PipelineOptions:
        return self._options

    def run(self, steps: tuple[PipelineStep, ...] | None = None) -> PipelineResult:
        selected_steps = steps or self._options.resolved_steps()
        self._validate_steps(selected_steps)

        if not self._options.skip_services and self._needs_service_check(selected_steps):
            ensure_services_ready(project_root=self._project_root)

        if self._options.from_step > 1:
            self._context.load_artifact_state(from_step=self._options.from_step)

        executed: list[int] = []
        for step in selected_steps:
            handler = self._step_handlers.get(step)
            if handler is None:
                raise PipelineConfigurationError(f"No handler registered for step {step.name}.")

            try:
                handler.execute(self._context, self._options)
            except PipelineStepError:
                raise
            except Exception as error:
                raise PipelineStepError(f"Step {step.name} failed: {error}") from error

            executed.append(step.value)

        return PipelineResult(context=self._context, steps_executed=tuple(executed))

    def _needs_service_check(self, steps: tuple[PipelineStep, ...]) -> bool:
        service_steps = {
            PipelineStep.BUILD_GRAPH,
            PipelineStep.RANK_PROJECTS,
        }
        return any(step in service_steps for step in steps)

    def _validate_steps(self, steps: tuple[PipelineStep, ...]) -> None:
        if not steps:
            raise PipelineConfigurationError("At least one pipeline step must be selected.")

        if self._options.from_step < 1 or self._options.from_step > 6:
            raise PipelineConfigurationError("from_step must be between 1 and 6.")

        if PipelineStep.PARSE_RESUME in steps and self._context.resume_path is None:
            raise PipelineConfigurationError("resume_path is required when running PARSE_RESUME.")

        if self._context.companies_path is None and self._context.companies is None:
            if any(
                step in steps
                for step in (
                    PipelineStep.BUILD_GRAPH,
                    PipelineStep.RANK_PROJECTS,
                    PipelineStep.GENERATE_DRAFT,
                )
            ):
                raise PipelineConfigurationError("companies_path or companies data is required.")

        self._context.output_dir = self._options.output_dir
        self._context.ensure_output_dir()
