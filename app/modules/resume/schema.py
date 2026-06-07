from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ResumeLinks:
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    github: str | None = None
    linkedin: str | None = None
    portfolio: str | None = None
    urls: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "emails": self.emails,
            "phones": self.phones,
            "github": self.github,
            "linkedin": self.linkedin,
            "portfolio": self.portfolio,
            "urls": self.urls,
        }


@dataclass(frozen=True)
class ParsedResume:
    filename: str | None
    file_extension: str
    raw_text: str
    candidate_name: str | None
    summary: str
    skills: list[str]
    experience: list[str]
    projects: list[str]
    achievements: list[str]
    research: list[str]
    education: list[str]
    links: ResumeLinks
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "file_extension": self.file_extension,
            "candidate_name": self.candidate_name,
            "summary": self.summary,
            "skills": self.skills,
            "experience": self.experience,
            "projects": self.projects,
            "achievements": self.achievements,
            "research": self.research,
            "education": self.education,
            "links": self.links.to_dict(),
            "raw_text": self.raw_text,
            "metadata": self.metadata,
        }
