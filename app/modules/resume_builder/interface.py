from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.modules.resume_builder.model import ProfessionalProfile, ResumeDocument


class ResumeBuilderRepository(Protocol):
    def get_profile(self) -> ProfessionalProfile: ...
    def save_profile(self, profile: ProfessionalProfile) -> ProfessionalProfile: ...
    def get_document(self, document_id: str) -> ResumeDocument | None: ...
    def save_document(self, document: ResumeDocument) -> ResumeDocument: ...


class LatexCompiler(Protocol):
    def compile(self, source: str, output_dir: Path) -> bytes: ...
