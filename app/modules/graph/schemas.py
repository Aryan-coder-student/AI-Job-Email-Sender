from __future__ import annotations

from typing import Literal

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, field_validator


class GitHubGraphEnrichmentSchema(BaseModel):
    capabilities: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    problems_solved: list[str] = Field(default_factory=list)
    complexity: str | None = None
    business_impact: str | None = None
    impact_signals: list[str] = Field(default_factory=list)

    @field_validator("capabilities", "domains", "problems_solved", "impact_signals", mode="before")
    @classmethod
    def coerce_nullable_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []


class EmployerEnrichmentSchema(BaseModel):
    company_domains: list[str] = Field(default_factory=list)
    company_looked_for_capabilities: list[str] = Field(default_factory=list)
    company_looked_for_technologies: list[str] = Field(default_factory=list)
    job_required_capabilities: list[str] = Field(default_factory=list)
    job_required_technologies: list[str] = Field(default_factory=list)
    industry: str | None = None
    enrichment_source: Literal["company", "job", "both"] = "company"

    @field_validator(
        "company_domains",
        "company_looked_for_capabilities",
        "company_looked_for_technologies",
        "job_required_capabilities",
        "job_required_technologies",
        mode="before",
    )
    @classmethod
    def coerce_nullable_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []


class ResumeExperienceEnrichmentSchema(BaseModel):
    index: int
    capabilities: list[str] = Field(default_factory=list)


class ResumeAchievementEnrichmentSchema(BaseModel):
    index: int
    capabilities: list[str] = Field(default_factory=list)


class ResumeProjectLinkSchema(BaseModel):
    index: int
    matched_repo_link: str | None = None


class ResumeGraphEnrichmentSchema(BaseModel):
    experience_capabilities: list[ResumeExperienceEnrichmentSchema] = Field(default_factory=list)
    achievement_capabilities: list[ResumeAchievementEnrichmentSchema] = Field(default_factory=list)
    project_links: list[ResumeProjectLinkSchema] = Field(default_factory=list)
    inferred_skill_technologies: list[str] = Field(default_factory=list)


github_graph_enrichment_parser = PydanticOutputParser(pydantic_object=GitHubGraphEnrichmentSchema)
employer_enrichment_parser = PydanticOutputParser(pydantic_object=EmployerEnrichmentSchema)
resume_graph_enrichment_parser = PydanticOutputParser(pydantic_object=ResumeGraphEnrichmentSchema)
