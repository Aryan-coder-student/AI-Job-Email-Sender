from __future__ import annotations

from enum import IntEnum


class PipelineStep(IntEnum):
    PARSE_RESUME = 1
    PARSE_GITHUB = 2
    BUILD_GRAPH = 3
    RANK_PROJECTS = 4
    GENERATE_DRAFT = 5
    PROCESS_MAIL_QUEUE = 6


ALL_PIPELINE_STEPS: tuple[PipelineStep, ...] = tuple(PipelineStep)
