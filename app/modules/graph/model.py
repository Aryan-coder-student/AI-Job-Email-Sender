from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

NodeLabel = Literal[
    "Candidate",
    "Project",
    "Technology",
    "Capability",
    "Domain",
    "Experience",
    "Achievement",
    "Company",
    "Role",
    "JobOpening",
    "OntologyTerm",
]

RelationshipType = Literal[
    "OWNS",
    "HAS",
    "USES",
    "DEMONSTRATES",
    "BELONGS_TO",
    "AT",
    "OPERATES_IN",
    "LOOKS_FOR",
    "REQUIRES",
    "FOR",
    "IS_A",
]


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    label: NodeLabel
    name: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    source_id: str
    target_id: str
    relationship: RelationshipType
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MatchPath:
    company_name: str
    project_name: str
    path_labels: list[str]
    graph_score: float
    match_source: str = "graph"

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "project_name": self.project_name,
            "path_labels": self.path_labels,
            "graph_score": self.graph_score,
            "match_source": self.match_source,
        }


@dataclass(frozen=True)
class ProjectMatch:
    project_id: str
    project_name: str
    graph_score: float
    embedding_score: float
    llm_score: float
    final_score: float
    explanation: str
    paths: list[MatchPath] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "graph_score": self.graph_score,
            "embedding_score": self.embedding_score,
            "llm_score": self.llm_score,
            "final_score": self.final_score,
            "explanation": self.explanation,
            "paths": [path.to_dict() for path in self.paths],
        }


@dataclass(frozen=True)
class EmployerProfile:
    company_id: str
    company_name: str
    company_description: str | None = None
    job_description: str | None = None
    role: str | None = None
    job_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "company_description": self.company_description,
            "job_description": self.job_description,
            "role": self.role,
            "job_id": self.job_id,
        }


@dataclass(frozen=True)
class GraphBuildResult:
    nodes_upserted: int
    edges_upserted: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes_upserted": self.nodes_upserted,
            "edges_upserted": self.edges_upserted,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class GitHubGraphEnrichment:
    capabilities: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    problems_solved: list[str] = field(default_factory=list)
    complexity: str | None = None
    business_impact: str | None = None
    impact_signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "capabilities": self.capabilities,
            "domains": self.domains,
            "problems_solved": self.problems_solved,
            "complexity": self.complexity,
            "business_impact": self.business_impact,
            "impact_signals": self.impact_signals,
        }


@dataclass(frozen=True)
class EmployerEnrichmentInput:
    company_name: str
    company_description: str | None = None
    job_description: str | None = None
    role: str | None = None


@dataclass(frozen=True)
class EmployerEnrichmentResult:
    company_domains: list[str] = field(default_factory=list)
    company_looked_for_capabilities: list[str] = field(default_factory=list)
    company_looked_for_technologies: list[str] = field(default_factory=list)
    job_required_capabilities: list[str] = field(default_factory=list)
    job_required_technologies: list[str] = field(default_factory=list)
    industry: str | None = None
    enrichment_source: Literal["company", "job", "both"] = "company"

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_domains": self.company_domains,
            "company_looked_for_capabilities": self.company_looked_for_capabilities,
            "company_looked_for_technologies": self.company_looked_for_technologies,
            "job_required_capabilities": self.job_required_capabilities,
            "job_required_technologies": self.job_required_technologies,
            "industry": self.industry,
            "enrichment_source": self.enrichment_source,
        }


@dataclass(frozen=True)
class ResumeGraphEnrichment:
    experience_capabilities: dict[int, list[str]] = field(default_factory=dict)
    achievement_capabilities: dict[int, list[str]] = field(default_factory=dict)
    project_links: dict[int, str | None] = field(default_factory=dict)
    skill_technologies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "experience_capabilities": self.experience_capabilities,
            "achievement_capabilities": self.achievement_capabilities,
            "project_links": self.project_links,
            "skill_technologies": self.skill_technologies,
        }
