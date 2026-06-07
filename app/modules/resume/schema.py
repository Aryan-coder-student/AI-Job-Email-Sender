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
class ResumeExperience:
    company_name: str | None = None
    date: str | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "date": self.date,
            "description": self.description,
        }


@dataclass(frozen=True)
class ResumeProject:
    project_name: str | None = None
    link: str | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "link": self.link,
            "description": self.description,
        }


@dataclass(frozen=True)
class ResumeCourse:
    name: str | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
        }


@dataclass(frozen=True)
class ResumeCertification:
    name: str | None = None
    link: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "link": self.link,
        }


@dataclass(frozen=True)
class ParsedResume:
    filename: str | None
    file_extension: str
    raw_text: str
    candidate_name: str | None
    summary: str
    skills: list[str]
    experience: list[ResumeExperience]
    projects: list[ResumeProject]
    courses: list[ResumeCourse]
    certifications: list[ResumeCertification]
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
            "experience": [e.to_dict() for e in self.experience],
            "projects": [p.to_dict() for p in self.projects],
            "courses": [c.to_dict() for c in self.courses],
            "certifications": [c.to_dict() for c in self.certifications],
            "achievements": self.achievements,
            "research": self.research,
            "education": self.education,
            "links": self.links.to_dict(),
            "raw_text": self.raw_text,
            "metadata": self.metadata,
        }
