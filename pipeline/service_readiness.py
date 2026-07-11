from __future__ import annotations

import subprocess
from collections.abc import Iterable
from pathlib import Path

from pipeline.exceptions import PipelineConfigurationError, PipelineStepError
from pipeline.steps.base import BaseStepHandler
from pipeline.types import PipelineStep

StepExecutionPlan = Iterable[tuple[PipelineStep, BaseStepHandler]]


def ensure_required_services_ready(
    *,
    project_root: Path,
    skip_services: bool,
    execution_plan: StepExecutionPlan,
) -> None:
    if skip_services:
        return

    if _requires_services(execution_plan):
        ensure_services_ready(project_root=project_root)


def ensure_services_ready(*, project_root: Path) -> None:
    script_path = project_root / "scripts" / "wait_for_services.sh"
    _validate_service_check_script(script_path)

    result = subprocess.run(
        [str(script_path)],
        cwd=project_root,
        check=False,
    )
    _validate_service_check_returncode(result.returncode)


def _requires_services(execution_plan: StepExecutionPlan) -> bool:
    return any(handler.requires_services for _step, handler in execution_plan)


def _validate_service_check_script(path: Path) -> None:
    if not path.is_file():
        raise PipelineConfigurationError(f"Missing service check script: {path}")


def _validate_service_check_returncode(returncode: int) -> None:
    if returncode != 0:
        raise PipelineStepError("Infrastructure services are not ready.")
