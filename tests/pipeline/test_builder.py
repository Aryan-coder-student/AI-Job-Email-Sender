from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pipeline.builder import ApplicationPipelineBuilder
from pipeline.config import PipelineOptions
from pipeline.context import PipelineContext
from pipeline.exceptions import PipelineConfigurationError
from pipeline.types import PipelineStep


def test_builder_requires_companies_for_graph_step() -> None:
    builder = (
        ApplicationPipelineBuilder()
        .with_resume("resume.pdf")
        .with_options(
            PipelineOptions(steps=(PipelineStep.BUILD_GRAPH,), output_dir=Path("data"))
        )
    )

    with pytest.raises(PipelineConfigurationError, match="companies"):
        builder.build().run()


def test_builder_loads_companies_from_path(tmp_path: Path) -> None:
    companies_file = tmp_path / "companies.json"
    companies_file.write_text('[{"company_name": "Acme"}]\n', encoding="utf-8")

    pipeline = (
        ApplicationPipelineBuilder()
        .with_companies(companies_file)
        .with_options(PipelineOptions(output_dir=tmp_path))
        .build()
    )

    assert pipeline.context.companies == [{"company_name": "Acme"}]


def test_options_resolved_steps_honors_from_step() -> None:
    options = PipelineOptions(from_step=5)

    assert options.resolved_steps() == (
        PipelineStep.GENERATE_DRAFT,
        PipelineStep.PROCESS_MAIL_QUEUE,
    )


def test_run_executes_only_selected_handlers(tmp_path: Path) -> None:
    handler = MagicMock()
    handler.step = PipelineStep.PARSE_RESUME

    companies_file = tmp_path / "companies.json"
    companies_file.write_text('[{"company_name": "Acme"}]\n', encoding="utf-8")

    pipeline = (
        ApplicationPipelineBuilder(project_root=tmp_path)
        .with_resume(tmp_path / "resume.pdf")
        .with_companies(companies_file)
        .with_step_handlers({PipelineStep.PARSE_RESUME: handler})
        .with_options(
            PipelineOptions(
                steps=(PipelineStep.PARSE_RESUME,),
                output_dir=tmp_path,
                skip_services=True,
            )
        )
        .build()
    )

    result = pipeline.run()

    handler.execute.assert_called_once()
    assert result.steps_executed == (PipelineStep.PARSE_RESUME.value,)
