from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.modules.company_imports.model import CompanyImportPreview


class CompanyImportRepository:
    def __init__(self, *, output_dir: Path) -> None:
        self.output_dir = output_dir

    def save_preview(self, preview: CompanyImportPreview) -> None:
        imports_dir = self.output_dir / "imports"
        imports_dir.mkdir(parents=True, exist_ok=True)
        preview_path = imports_dir / f"{preview.import_id}.json"
        preview_path.write_text(
            f"{json.dumps(preview.to_dict(), indent=2, ensure_ascii=False)}\n",
            encoding="utf-8",
        )

    def load_preview(self, import_id: str) -> dict[str, Any] | None:
        preview_path = self.output_dir / "imports" / f"{import_id}.json"
        if not preview_path.is_file():
            return None

        return json.loads(preview_path.read_text(encoding="utf-8"))
