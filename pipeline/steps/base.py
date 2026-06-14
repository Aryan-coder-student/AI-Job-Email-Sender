from __future__ import annotations

from typing import Protocol

from pipeline.config import PipelineOptions
from pipeline.context import PipelineContext
from pipeline.types import PipelineStep


class StepHandler(Protocol):
    step: PipelineStep

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None: ...
