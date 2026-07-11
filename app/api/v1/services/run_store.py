from app.modules.runs.model import PipelineRunRecord, PipelineStepRecord
from app.modules.runs.service import PipelineRunStore

_RUN_STORE = PipelineRunStore()


def get_run_store() -> PipelineRunStore:
    return _RUN_STORE


__all__ = [
    "PipelineRunRecord",
    "PipelineRunStore",
    "PipelineStepRecord",
    "get_run_store",
]
