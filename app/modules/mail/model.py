from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MailAttachment:
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "content_type": self.content_type,
            "size_bytes": len(self.content),
        }


@dataclass(frozen=True)
class MailMessage:
    to: list[str]
    subject: str
    body_text: str
    body_html: str | None = None
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    attachments: list[MailAttachment] = field(default_factory=list)
    reply_to: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "to": self.to,
            "subject": self.subject,
            "body_text": self.body_text,
            "body_html": self.body_html,
            "cc": self.cc,
            "bcc": self.bcc,
            "attachments": [attachment.to_dict() for attachment in self.attachments],
            "reply_to": self.reply_to,
        }


@dataclass(frozen=True)
class SendMailResult:
    provider: str
    recipients: list[str]
    message_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "recipients": self.recipients,
            "message_id": self.message_id,
            "metadata": self.metadata,
        }
