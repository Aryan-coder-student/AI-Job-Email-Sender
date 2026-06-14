from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field


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
            "experience": [experience.to_dict() for experience in self.experience],
            "projects": [project.to_dict() for project in self.projects],
            "courses": [course.to_dict() for course in self.courses],
            "certifications": [certification.to_dict() for certification in self.certifications],
            "achievements": self.achievements,
            "research": self.research,
            "education": self.education,
            "links": self.links.to_dict(),
            "raw_text": self.raw_text,
            "metadata": self.metadata,
        }


class ResumeLinksSchema(BaseModel):
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    github: str | None = None
    linkedin: str | None = None
    portfolio: str | None = None
    urls: list[str] = Field(default_factory=list)


class ExperienceSchema(BaseModel):
    company_name: str | None = Field(default=None, description="Company or organization name.")
    date: str | None = Field(default=None, description="Range of dates, e.g. '1/2022 - 4/2022'.")
    description: str | None = Field(
        default=None,
        description="Full bullet point descriptions of responsibilities.",
    )


class ProjectSchema(BaseModel):
    project_name: str | None = Field(default=None, description="Project name.")
    link: str | None = Field(default=None, description="Link or URL to the project if available.")
    description: str | None = Field(default=None, description="Full description of the project.")


class CourseSchema(BaseModel):
    name: str | None = Field(default=None, description="Name of the course.")
    description: str | None = Field(default=None, description="Description of the course if available.")


class CertificationSchema(BaseModel):
    name: str | None = Field(default=None, description="Name of the certification.")
    link: str | None = Field(default=None, description="Link or URL to the certificate if available.")


class ResumeStructureSchema(BaseModel):
    candidate_name: str | None = Field(
        default=None,
        description="Candidate name exactly as shown in the resume.",
    )
    summary: str = Field(
        default="",
        description="Concise factual summary, max 3 sentences.",
    )
    skills: list[str] = Field(
        default_factory=list,
        description="List of individual skills.",
    )
    experience: list[ExperienceSchema] = Field(
        default_factory=list,
        description="List of work experiences.",
    )
    projects: list[ProjectSchema] = Field(
        default_factory=list,
        description="List of projects.",
    )
    courses: list[CourseSchema] = Field(
        default_factory=list,
        description="List of courses.",
    )
    certifications: list[CertificationSchema] = Field(
        default_factory=list,
        description="List of certifications.",
    )
    achievements: list[str] = Field(
        default_factory=list,
        description="List of achievements, awards, and recognitions including full details.",
    )
    research: list[str] = Field(
        default_factory=list,
        description="List of research work, papers, or publications with descriptions.",
    )
    education: list[str] = Field(
        default_factory=list,
        description="List of educational qualifications including degree, institution, and dates.",
    )
    links: ResumeLinksSchema = Field(default_factory=ResumeLinksSchema)


resume_parser = PydanticOutputParser(pydantic_object=ResumeStructureSchema)
