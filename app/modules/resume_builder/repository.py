from __future__ import annotations

import json
from pathlib import Path

from app.modules.resume_builder.model import ProfessionalProfile, ResumeDocument


class JsonResumeBuilderRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.documents_dir = root / "documents"

    def get_profile(self) -> ProfessionalProfile:
        path = self.root / "profile.json"
        if not path.exists():
            return ProfessionalProfile()
        return ProfessionalProfile.model_validate_json(path.read_text(encoding="utf-8"))

    def save_profile(self, profile: ProfessionalProfile) -> ProfessionalProfile:
        self.root.mkdir(parents=True, exist_ok=True)
        self._write(self.root / "profile.json", profile.model_dump_json(indent=2))
        return profile

    def get_document(self, document_id: str) -> ResumeDocument | None:
        path = self.documents_dir / f"{document_id}.json"
        if not path.exists():
            return None
        return ResumeDocument.model_validate_json(path.read_text(encoding="utf-8"))

    def save_document(self, document: ResumeDocument) -> ResumeDocument:
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self._write(self.documents_dir / f"{document.id}.json", document.model_dump_json(indent=2))
        return document

    @staticmethod
    def _write(path: Path, content: str) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)
