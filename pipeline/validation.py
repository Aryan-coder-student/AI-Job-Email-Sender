from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, TypeVar

from pipeline.exceptions import PipelineConfigurationError
from pipeline.types import PipelineStep

if TYPE_CHECKING:
    from pipeline.config import PipelineOptions
    from pipeline.context import PipelineContext
    from pipeline.steps.base import BaseStepHandler

T = TypeVar("T")


def require_value(value: T | None, message: str) -> T:
    if value is None:
        raise PipelineConfigurationError(message)
    return value


def validate_steps_selected(steps: tuple[PipelineStep, ...]) -> None:
    if not steps:
        raise PipelineConfigurationError("At least one pipeline step must be selected.")


def validate_from_step(from_step: int) -> None:
    valid_steps = set(PipelineStep)
    if from_step not in valid_steps:
        first_step = min(valid_steps).value
        final_step = max(valid_steps).value
        raise PipelineConfigurationError(
            f"from_step must be between {first_step} and {final_step}."
        )


def validate_step_handlers_registered(
    steps: tuple[PipelineStep, ...],
    handlers: Mapping[PipelineStep, object],
) -> None:
    missing_steps = tuple(step.name for step in steps if step not in handlers)
    if missing_steps:
        raise PipelineConfigurationError(
            f"No handler registered for step(s): {', '.join(missing_steps)}."
        )


def validate_execution_plan(
    execution_plan: tuple[tuple[PipelineStep, BaseStepHandler], ...],
    context: PipelineContext,
    options: PipelineOptions,
) -> None:
    for _step, handler in execution_plan:
        handler.validate(context, options)


def validate_resume_path(context: PipelineContext) -> Path:
    return require_value(
        context.resume_path,
        "resume_path is required when running PARSE_RESUME.",
    )


def validate_companies_loaded(context: PipelineContext) -> list[dict[str, Any]]:
    return require_value(
        context.companies,
        "companies data must be loaded by the builder.",
    )


def validate_existing_file(path: Path, message: str) -> Path:
    if not path.is_file():
        raise PipelineConfigurationError(message)
    return path


def validate_artifact_exists(path: Path, name: str) -> Path:
    return validate_existing_file(path, f"Missing {name} artifact: {path}")


def validate_companies_file(path: Path) -> Path:
    return validate_existing_file(path, f"Companies file not found: {path}")
