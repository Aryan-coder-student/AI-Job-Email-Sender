from __future__ import annotations

from abc import ABC, abstractmethod

from pipeline.config import PipelineOptions
from pipeline.context import PipelineContext
from pipeline.types import PipelineStep


class BaseStepHandler(ABC):
    step: PipelineStep
    requires_services: bool = False

    def validate(self, context: PipelineContext, options: PipelineOptions) -> None:
        pass

    @abstractmethod
    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        pass
