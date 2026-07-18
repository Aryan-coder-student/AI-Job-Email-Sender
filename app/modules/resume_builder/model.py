from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ProfileItem(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    title: str
    subtitle: str = ""
    date: str = ""
    description: str = ""
    skills: list[str] = Field(default_factory=list)
    link: str | None = None


class ProfessionalProfile(BaseModel):
    name: str = ""
    headline: str = ""
    summary: str = ""
    email: str = ""
    phone: str = ""
    links: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    experiences: list[ProfileItem] = Field(default_factory=list)
    projects: list[ProfileItem] = Field(default_factory=list)
    education: list[ProfileItem] = Field(default_factory=list)
    certifications: list[ProfileItem] = Field(default_factory=list)
    publications: list[ProfileItem] = Field(default_factory=list)


class JobRequirements(BaseModel):
    company_name: str
    role: str = ""
    description: str = ""
    required_skills: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    experience_level: str | None = None


class Recommendation(BaseModel):
    item_id: str
    section: Literal["experiences", "projects", "certifications", "publications"]
    title: str
    score: float
    matched_keywords: list[str] = Field(default_factory=list)
    reason: str


class ResumeDocument(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    company_name: str
    role: str = ""
    template: Literal["classic", "compact"] = "classic"
    section_order: list[str] = Field(
        default_factory=lambda: ["summary", "skills", "experience", "projects", "education", "certifications", "publications"]
    )
    selected_item_ids: list[str] = Field(default_factory=list)
    profile: ProfessionalProfile
    recommendations: list[Recommendation] = Field(default_factory=list)
    custom_latex: str | None = None
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RecommendationRequest(BaseModel):
    job: JobRequirements
    limit: int = Field(default=10, ge=5, le=10)


class ResumeDocumentRequest(BaseModel):
    job: JobRequirements
    source_latex: str | None = None
    template: Literal["classic", "compact"] = "classic"
    recommendation_limit: int = Field(default=10, ge=5, le=10)


class PipelineTailorRequest(BaseModel):
    company_name: str
    source_latex: str
    recommendation_limit: int = Field(default=10, ge=5, le=10)


class LatexUpdateRequest(BaseModel):
    custom_latex: str | None = None
    template: Literal["classic", "compact"] | None = None
    section_order: list[str] | None = None
    selected_item_ids: list[str] | None = None
    profile: ProfessionalProfile | None = None
