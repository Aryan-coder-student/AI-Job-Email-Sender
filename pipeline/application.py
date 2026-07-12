from __future__ import annotations

from pathlib import Path
from typing import Mapping, Protocol

from pipeline.config import PipelineOptions
from pipeline.context import PipelineContext, PipelineResult
from pipeline.exceptions import PipelineStepError
from pipeline.service_readiness import ensure_required_services_ready
from pipeline.steps.base import BaseStepHandler
from pipeline.steps.handlers import (
    BuildGraphStep,
    GenerateDraftStep,
    ParseGitHubStep,
    ParseResumeStep,
    ProcessMailQueueStep,
    RankProjectsStep,
)
from pipeline.types import PipelineStep
from pipeline.validation import (
    validate_execution_plan,
    validate_from_step,
    validate_step_handlers_registered,
    validate_steps_selected,
)

DEFAULT_STEP_HANDLERS: Mapping[PipelineStep, BaseStepHandler] = {
    PipelineStep.PARSE_RESUME: ParseResumeStep(),
    PipelineStep.PARSE_GITHUB: ParseGitHubStep(),
    PipelineStep.BUILD_GRAPH: BuildGraphStep(),
    PipelineStep.RANK_PROJECTS: RankProjectsStep(),
    PipelineStep.GENERATE_DRAFT: GenerateDraftStep(),
    PipelineStep.PROCESS_MAIL_QUEUE: ProcessMailQueueStep(),
}


class PipelineStepObserver(Protocol):
    def step_started(self, step: PipelineStep) -> None: ...

    def step_completed(self, step: PipelineStep) -> None: ...

    def step_failed(self, step: PipelineStep, error: str) -> None: ...

class _NoopStepObserver:
    def step_started(self, step: PipelineStep) -> None:
        pass

    def step_completed(self, step: PipelineStep) -> None:
        pass

    def step_failed(self, step: PipelineStep, error: str) -> None:
        pass


StepExecutionPlan = tuple[tuple[PipelineStep, BaseStepHandler], ...]


class ApplicationPipeline:
    def __init__(
        self,
        *,
        context: PipelineContext,
        options: PipelineOptions,
        project_root: Path,
        step_handlers: Mapping[PipelineStep, BaseStepHandler] | None = None,
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

    def run(
        self,
        steps: tuple[PipelineStep, ...] | None = None,
        *,
        observer: PipelineStepObserver | None = None,
    ) -> PipelineResult:
        execution_plan = self._prepare_execution_plan(self._selected_steps(steps))
        step_observer = observer or _NoopStepObserver()
        executed_steps = tuple(
            self._execute_step(step, handler, step_observer)
            for step, handler in execution_plan
        )

        return PipelineResult(context=self._context, steps_executed=executed_steps)

    def _selected_steps(
        self,
        steps: tuple[PipelineStep, ...] | None,
    ) -> tuple[PipelineStep, ...]:
        return self._options.resolved_steps() if steps is None else steps

    def _prepare_execution_plan(self, steps: tuple[PipelineStep, ...]) -> StepExecutionPlan:
        validate_steps_selected(steps)
        validate_from_step(self._options.from_step)

        self._context.output_dir = self._options.output_dir
        self._context.ensure_output_dir()
        execution_plan = self._execution_plan_for(steps)
        validate_execution_plan(execution_plan, self._context, self._options)
        ensure_required_services_ready(
            project_root=self._project_root,
            skip_services=self._options.skip_services,
            execution_plan=execution_plan,
        )
        self._context.load_artifact_state(from_step=self._options.from_step)
        return execution_plan

    def _execution_plan_for(self, steps: tuple[PipelineStep, ...]) -> StepExecutionPlan:
        validate_step_handlers_registered(steps, self._step_handlers)
        return tuple((step, self._step_handlers[step]) for step in steps)

    def _execute_step(
        self,
        step: PipelineStep,
        handler: BaseStepHandler,
        observer: PipelineStepObserver,
    ) -> int:
        try:
            observer.step_started(step)
            handler.execute(self._context, self._options)
            observer.step_completed(step)
        except PipelineStepError as error:
            observer.step_failed(step, str(error))
            raise
        except Exception as error:
            observer.step_failed(step, str(error))
            raise PipelineStepError(f"Step {step.name} failed: {error}") from error

        return step.value
