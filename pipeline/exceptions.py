from __future__ import annotations


class PipelineError(Exception):
    """Base error for pipeline orchestration."""


class PipelineConfigurationError(PipelineError):
    """Raised when pipeline inputs or options are invalid."""


class PipelineStepError(PipelineError):
    """Raised when a pipeline step fails."""
