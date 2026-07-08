from __future__ import annotations

from pydantic import BaseModel, Field


class ResumeRunRequest(BaseModel):
    from_step: str | None = None


class DraftUpdateRequest(BaseModel):
    to: str | None = None
    subject: str | None = None
    body_text: str | None = None
    body_html: str | None = None


class ProcessMailRequest(BaseModel):
    dry_run: bool = True
    limit: int = Field(default=10, ge=1, le=100)
