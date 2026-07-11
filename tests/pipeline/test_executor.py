from __future__ import annotations

from pathlib import Path

from pipeline.executor import PipelineExecutionRequest, PipelineExecutionService
from pipeline.types import PipelineStep


def test_execution_service_runs_requested_steps_once(monkeypatch, tmp_path: Path) -> None:
    pipeline = _FakePipeline()
    request = PipelineExecutionRequest(
        resume_path=tmp_path / "resume.pdf",
        companies_path=tmp_path / "companies.json",
        output_dir=tmp_path,
        target_company="Acme",
        steps=(PipelineStep.PARSE_RESUME, PipelineStep.PARSE_GITHUB),
    )
    observer = _RecordingExecutionObserver()
    monkeypatch.setattr("pipeline.executor._build_pipeline", lambda request: pipeline)

    PipelineExecutionService().execute(request=request, observer=observer)

    assert pipeline.run_calls == [request.steps]
    assert observer.events == [
        ("pipeline_started", None),
        ("step_started", PipelineStep.PARSE_RESUME),
        ("step_completed", PipelineStep.PARSE_RESUME),
        ("step_started", PipelineStep.PARSE_GITHUB),
        ("step_completed", PipelineStep.PARSE_GITHUB),
        ("pipeline_completed", None),
    ]


class _FakePipeline:
    def __init__(self) -> None:
        self.run_calls: list[tuple[PipelineStep, ...]] = []

    def run(self, *, steps, observer) -> None:
        self.run_calls.append(steps)
        for step in steps:
            observer.step_started(step)
            observer.step_completed(step)


class _RecordingExecutionObserver:
    def __init__(self) -> None:
        self.events: list[tuple[str, PipelineStep | None]] = []

    def pipeline_started(self) -> None:
        self.events.append(("pipeline_started", None))

    def pipeline_completed(self) -> None:
        self.events.append(("pipeline_completed", None))

    def pipeline_failed(self, error: str) -> None:
        self.events.append(("pipeline_failed", None))

    def step_started(self, step: PipelineStep) -> None:
        self.events.append(("step_started", step))

    def step_completed(self, step: PipelineStep) -> None:
        self.events.append(("step_completed", step))
