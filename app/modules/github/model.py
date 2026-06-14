from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, field_validator


def _coerce_nullable_list(value: Any) -> list[Any]:
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, str) and value.strip():
        return [value.strip()]

    return []


@dataclass(frozen=True)
class GitHubRepoReadme:
    repo_name: str
    repo_link: str
    raw_readme: str


@dataclass(frozen=True)
class GitHubTechStack:
    backend: list[str] = field(default_factory=list)
    frontend: list[str] = field(default_factory=list)
    ai_ml: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "frontend": self.frontend,
            "ai_ml": self.ai_ml,
        }


@dataclass(frozen=True)
class ParsedGitHubProject:
    repo_name: str
    repo_link: str
    deployed_link: str | None
    summary: str
    tech_stack: GitHubTechStack
    non_tech_tags: list[str]
    raw_readme: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_name": self.repo_name,
            "repo_link": self.repo_link,
            "deployed_link": self.deployed_link,
            "summary": self.summary,
            "tech_stack": self.tech_stack.to_dict(),
            "non_tech_tags": self.non_tech_tags,
            "raw_readme": self.raw_readme,
        }


@dataclass(frozen=True)
class ParsedGitHubProfile:
    github_username: str
    github_url: str
    projects: list[ParsedGitHubProject]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "github_username": self.github_username,
            "github_url": self.github_url,
            "projects": [project.to_dict() for project in self.projects],
            "metadata": self.metadata,
        }


class TechStackSchema(BaseModel):
    backend: list[str] = Field(
        default_factory=list,
        description="Backend languages, frameworks, and server-side tools inferred from the README.",
    )
    frontend: list[str] = Field(
        default_factory=list,
        description="Frontend languages, frameworks, and UI libraries inferred from the README.",
    )
    ai_ml: list[str] = Field(
        default_factory=list,
        description="AI, ML, data science, and LLM-related tools inferred from the README.",
    )

    @field_validator("backend", "frontend", "ai_ml", mode="before")
    @classmethod
    def coerce_nullable_lists(cls, value: Any) -> list[Any]:
        return _coerce_nullable_list(value)


class GitHubProjectStructureSchema(BaseModel):
    summary: str = Field(
        default="",
        description="Concise project summary inferred from README purpose and features, max 3 sentences.",
    )
    tech_stack: TechStackSchema = Field(default_factory=TechStackSchema)
    non_tech_tags: list[str] = Field(
        default_factory=list,
        description="Non-technical domain or theme tags inferred from README context.",
    )
    deployed_link: str | None = Field(
        default=None,
        description="Live demo or deployment URL found or inferred from README links and badges.",
    )

    @field_validator("summary", mode="before")
    @classmethod
    def coerce_summary(cls, value: Any) -> str:
        if value is None:
            return ""

        return value

    @field_validator("non_tech_tags", mode="before")
    @classmethod
    def coerce_non_tech_tags(cls, value: Any) -> list[Any]:
        return _coerce_nullable_list(value)


github_project_parser = PydanticOutputParser(pydantic_object=GitHubProjectStructureSchema)
