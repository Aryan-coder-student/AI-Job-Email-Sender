from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pipeline.application import ApplicationPipeline
    from pipeline.builder import ApplicationPipelineBuilder
    from pipeline.config import PipelineOptions
    from pipeline.context import PipelineContext, PipelineResult
    from pipeline.exceptions import (
        PipelineConfigurationError,
        PipelineError,
        PipelineStepError,
    )
    from pipeline.executor import (
        PipelineExecutionObserver,
        PipelineExecutionRequest,
        PipelineExecutionService,
    )
    from pipeline.types import PipelineStep

__all__ = [
    "ApplicationPipeline",
    "ApplicationPipelineBuilder",
    "PipelineConfigurationError",
    "PipelineContext",
    "PipelineError",
    "PipelineOptions",
    "PipelineResult",
    "PipelineStep",
    "PipelineStepError",
    "PipelineExecutionObserver",
    "PipelineExecutionRequest",
    "PipelineExecutionService",
]

_EXPORTS = {
    "ApplicationPipeline": ("pipeline.application", "ApplicationPipeline"),
    "ApplicationPipelineBuilder": ("pipeline.builder", "ApplicationPipelineBuilder"),
    "PipelineConfigurationError": ("pipeline.exceptions", "PipelineConfigurationError"),
    "PipelineContext": ("pipeline.context", "PipelineContext"),
    "PipelineError": ("pipeline.exceptions", "PipelineError"),
    "PipelineExecutionObserver": ("pipeline.executor", "PipelineExecutionObserver"),
    "PipelineExecutionRequest": ("pipeline.executor", "PipelineExecutionRequest"),
    "PipelineExecutionService": ("pipeline.executor", "PipelineExecutionService"),
    "PipelineOptions": ("pipeline.config", "PipelineOptions"),
    "PipelineResult": ("pipeline.context", "PipelineResult"),
    "PipelineStep": ("pipeline.types", "PipelineStep"),
    "PipelineStepError": ("pipeline.exceptions", "PipelineStepError"),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module 'pipeline' has no attribute {name!r}")

    module_name, export_name = _EXPORTS[name]
    module = __import__(module_name, fromlist=[export_name])
    value = getattr(module, export_name)
    globals()[name] = value
    return value
