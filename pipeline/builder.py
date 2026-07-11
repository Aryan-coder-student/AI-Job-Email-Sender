from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

from app.modules.graph.serializers import load_json_file
from pipeline.application import DEFAULT_STEP_HANDLERS, ApplicationPipeline
from pipeline.config import PipelineOptions
from pipeline.context import PipelineContext
from pipeline.steps.base import BaseStepHandler
from pipeline.types import PipelineStep
from pipeline.validation import validate_companies_file


class ApplicationPipelineBuilder:
    def __init__(self, *, project_root: Path | None = None) -> None:
        self._project_root = project_root or Path.cwd()
        self._context = PipelineContext()
        self._options = PipelineOptions()
        self._step_handlers: Mapping[PipelineStep, BaseStepHandler] | None = None

    def with_resume(self, resume_path: str | Path) -> ApplicationPipelineBuilder:
        self._context.resume_path = Path(resume_path)
        return self

    def with_companies(self, companies_path: str | Path) -> ApplicationPipelineBuilder:
        self._context.companies_path = Path(companies_path)
        return self

    def with_target_company(self, company_name: str) -> ApplicationPipelineBuilder:
        self._options = replace(self._options, target_company=company_name)
        return self

    def with_recipient_email(self, email: str | None) -> ApplicationPipelineBuilder:
        self._options = replace(self._options, recipient_email=email)
        return self

    def with_output_dir(self, output_dir: str | Path) -> ApplicationPipelineBuilder:
        output_path = Path(output_dir)
        self._options = replace(self._options, output_dir=output_path)
        self._context.output_dir = output_path
        return self

    def with_steps(
        self,
        steps: list[PipelineStep] | tuple[PipelineStep, ...],
    ) -> ApplicationPipelineBuilder:
        self._options = replace(self._options, steps=tuple(steps))
        return self

    def with_options(self, options: PipelineOptions) -> ApplicationPipelineBuilder:
        self._options = options
        self._context.output_dir = options.output_dir
        return self

    def with_step_handlers(
        self,
        handlers: Mapping[PipelineStep, BaseStepHandler],
    ) -> ApplicationPipelineBuilder:
        self._step_handlers = handlers
        return self

    def build(self) -> ApplicationPipeline:
        self._load_companies_if_needed()

        return ApplicationPipeline(
            context=self._context,
            options=self._options,
            project_root=self._project_root,
            step_handlers=self._step_handlers or DEFAULT_STEP_HANDLERS,
        )

    def _load_companies_if_needed(self) -> None:
        companies_path = self._context.companies_path
        if companies_path is None or self._context.companies is not None:
            return

        self._context.companies = self._load_companies(companies_path)

    def _load_companies(self, companies_path: Path) -> list[dict[str, Any]]:
        return load_json_file(str(validate_companies_file(companies_path)))
