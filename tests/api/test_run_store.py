from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.api.v1.services.run_store import PipelineRunStore
from app.api.v1.services.system_status import build_system_status
from app.core.exceptions import InvalidExcelError
from app.core.settings import reset_settings
from app.modules.company_imports import preview_company_import
from app.modules.company_imports.service import preview_company_import_from_url
from app.modules.excel.parser import ParsedExcelRow, ParsedExcelSheet, ParsedExcelWorkbook
from pipeline.types import PipelineStep


def test_run_store_seeds_demo_run_from_artifacts(tmp_path: Path) -> None:
    (tmp_path / "parse_resume.json").write_text(
        json.dumps({"candidate_name": "Aryan"}),
        encoding="utf-8",
    )
    (tmp_path / "matches.json").write_text(
        json.dumps([{"project_name": "Demo"}]),
        encoding="utf-8",
    )

    store = PipelineRunStore(output_dir=tmp_path)

    runs = store.list_runs()
    assert runs[0]["run_id"] == "local-demo"
    assert runs[0]["steps"][0]["status"] == "completed"
    assert store.get_artifact("local-demo", "resume") == {"candidate_name": "Aryan"}


def test_run_store_creates_retry_and_resume_run(tmp_path: Path) -> None:
    store = PipelineRunStore(output_dir=tmp_path)

    run = store.create_run(
        config={"target_company": "Acme"},
        resume_filename="resume.pdf",
        companies_filename="companies.xlsx",
    )

    assert run["status"] == "created"
    assert run["config"]["resume_filename"] == "resume.pdf"
    assert store.retry_run(run["run_id"])["status"] == "running"
    resumed = store.resume_run(run["run_id"], from_step="rank_projects")
    assert "rank_projects" in resumed["logs"][-1]


def test_company_import_preview_parses_csv_and_flags_invalid_rows(tmp_path: Path) -> None:
    preview = preview_company_import(
        content=(
            b"Company,Role,Email\n"
            b"Acme,Backend,hr@acme.test\n"
            b"\n"
            b",Frontend,hr@example.test\n"
        ),
        filename="companies.csv",
        output_dir=tmp_path,
    )

    assert preview["total_rows"] == 2
    assert preview["valid_rows"] == 1
    assert preview["invalid_rows"] == 1
    assert preview["rows"][0]["normalized"]["company_name"] == "Acme"
    assert preview["rows"][1]["issues"] == ["Company name is required."]
    assert (tmp_path / "imports" / f"{preview['import_id']}.json").is_file()


def test_company_import_preview_parses_google_sheet_url(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workbook = ParsedExcelWorkbook(
        filename="google-sheet-sheet-id.xlsx",
        sheets=[
            ParsedExcelSheet(
                name="Companies",
                headers=["company", "role"],
                total_populated_rows=1,
                rows=[
                    ParsedExcelRow(
                        sheet_name="Companies",
                        row_number=2,
                        data={"company": "Acme", "role": "Backend"},
                        normalized={"company_name": "Acme", "role": "Backend"},
                    )
                ],
            )
        ],
    )
    monkeypatch.setattr(
        "app.modules.company_imports.service.parse_excel_from_url",
        lambda url, config: workbook,
    )

    preview = preview_company_import_from_url(
        url="https://docs.google.com/spreadsheets/d/sheet-id/edit#gid=1",
        output_dir=tmp_path,
    )

    assert preview["filename"] == "google-sheet-sheet-id.xlsx"
    assert preview["valid_rows"] == 1
    assert preview["rows"][0]["normalized"]["company_name"] == "Acme"
    assert preview["rows"][0]["source_sheet"] == "Companies"


def test_company_import_preview_rejects_invalid_json_rows(tmp_path: Path) -> None:
    with pytest.raises(InvalidExcelError, match="JSON company row 2 must be an object."):
        preview_company_import(
            content=b'[{"Company": "Acme"}, "not-a-company"]',
            filename="companies.json",
            output_dir=tmp_path,
        )


def test_run_store_persists_selected_companies(tmp_path: Path) -> None:
    store = PipelineRunStore(output_dir=tmp_path)
    run = store.create_run(
        config={"dry_run": True},
        selected_companies=[{"company_name": "Acme", "role": "Backend"}],
    )

    restored_store = PipelineRunStore(output_dir=tmp_path)
    restored_run = restored_store.get_run(run["run_id"])

    assert restored_run is not None
    assert restored_run["config"]["target_company"] == "Acme"
    assert restored_store.get_companies(run["run_id"]) == [
        {"company_name": "Acme", "role": "Backend"}
    ]


def test_run_store_executes_runs_through_pipeline_service(tmp_path: Path) -> None:
    executor = _FakePipelineExecutor()
    store = PipelineRunStore(output_dir=tmp_path, executor=executor)
    run = store.create_run(
        config={"target_company": "Acme", "dry_run": True},
        resume_filename="resume.txt",
        resume_content=b"Aryan Resume",
        selected_companies=[{"company_name": "Acme"}],
    )

    store.execute_run(run["run_id"])

    executed_request = executor.request
    completed_run = store.get_run(run["run_id"])
    assert executed_request is not None
    assert executed_request.target_company == "Acme"
    assert executed_request.resume_path.is_file()
    assert executed_request.companies_path.is_file()
    assert completed_run["status"] == "completed"
    assert completed_run["steps"][0]["status"] == "completed"


def test_system_status_masks_secret_values(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY_1", "secret")
    reset_settings()

    status = build_system_status()

    assert status["llm"]["configured"] is True
    assert status["llm"]["providers"]["groq"]["key_count"] == 1
    assert "secret" not in str(status)


class _FakePipelineExecutor:
    def __init__(self) -> None:
        self.request = None

    def execute(self, *, request, observer) -> None:
        self.request = request
        observer.pipeline_started()
        observer.step_started(PipelineStep.PARSE_RESUME)
        observer.step_completed(PipelineStep.PARSE_RESUME)
        observer.pipeline_completed()
