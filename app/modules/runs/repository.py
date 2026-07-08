from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.modules.runs.model import ARTIFACT_FILES, PipelineRunRecord


class JsonRunRepository:
    def __init__(self, *, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.runs_dir = output_dir / "runs"
        self.manifest_path = self.runs_dir / "runs.json"

    def load_runs(self) -> dict[str, PipelineRunRecord]:
        if not self.manifest_path.is_file():
            return {}

        payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            return {}

        runs: dict[str, PipelineRunRecord] = {}
        for item in payload:
            if not isinstance(item, dict):
                continue

            run = PipelineRunRecord.from_dict(item)
            runs[run.run_id] = run
        return runs

    def save_runs(self, runs: dict[str, PipelineRunRecord]) -> None:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        payload = [run.to_dict() for run in runs.values() if run.run_id != "local-demo"]
        self.manifest_path.write_text(
            f"{json.dumps(payload, indent=2, ensure_ascii=False)}\n",
            encoding="utf-8",
        )

    def run_dir(self, run_id: str) -> Path:
        return self.runs_dir / run_id

    def upload_dir(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "uploads"

    def artifact_dir(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "artifacts"

    def artifact_path(self, *, run: PipelineRunRecord, artifact_type: str) -> Path | None:
        filename = ARTIFACT_FILES.get(artifact_type)
        output_dir = path_from_config(run.config, "output_dir")
        if not filename or output_dir is None:
            return None

        return output_dir / filename

    def write_resume_upload(
        self,
        *,
        run_id: str,
        filename: str | None,
        content: bytes | None,
    ) -> Path | None:
        if not filename or not content:
            return None

        upload_dir = self.upload_dir(run_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        resume_path = upload_dir / Path(filename).name
        resume_path.write_bytes(content)
        return resume_path

    def write_companies(
        self,
        *,
        run_id: str,
        companies: list[dict[str, Any]],
    ) -> Path:
        artifact_dir = self.artifact_dir(run_id)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        companies_path = artifact_dir / "companies_sheet.json"
        companies_path.write_text(
            f"{json.dumps(companies, indent=2, ensure_ascii=False)}\n",
            encoding="utf-8",
        )
        return companies_path


def path_from_config(config: dict[str, Any], key: str) -> Path | None:
    value = config.get(key)
    return Path(str(value)) if value else None
