from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

DraftStatus = Literal["draft", "queued", "sent", "failed"]


@dataclass(frozen=True)
class DraftGenerationRequest:
    candidate_name: str | None
    candidate_summary: str | None
    candidate_skills: list[str]
    company_name: str
    company_record: dict[str, Any]
    top_match: dict[str, Any]
    recipient_email: str | None = None
    github_projects: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class EmailDraft:
    draft_id: str
    to: str
    subject: str
    body_text: str
    company_name: str
    project_name: str | None
    status: DraftStatus = "draft"
    body_html: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def new_id(cls) -> str:
        return str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "to": self.to,
            "subject": self.subject,
            "body_text": self.body_text,
            "body_html": self.body_html,
            "company_name": self.company_name,
            "project_name": self.project_name,
            "status": self.status,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> EmailDraft:
        return cls(
            draft_id=str(payload["draft_id"]),
            to=str(payload["to"]),
            subject=str(payload["subject"]),
            body_text=str(payload["body_text"]),
            body_html=payload.get("body_html"),
            company_name=str(payload["company_name"]),
            project_name=payload.get("project_name"),
            status=str(payload.get("status") or "draft"),
            metadata=dict(payload.get("metadata") or {}),
        )

    def with_status(self, status: DraftStatus, **metadata: Any) -> EmailDraft:
        merged_metadata = {**self.metadata, **metadata}
        return EmailDraft(
            draft_id=self.draft_id,
            to=self.to,
            subject=self.subject,
            body_text=self.body_text,
            body_html=self.body_html,
            company_name=self.company_name,
            project_name=self.project_name,
            status=status,
            metadata=merged_metadata,
        )


@dataclass(frozen=True)
class EnqueueResult:
    draft_id: str
    queue_key: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "queue_key": self.queue_key,
        }
