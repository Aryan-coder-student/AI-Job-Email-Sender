from __future__ import annotations

import hashlib
from typing import Any

from app.core.logger import get_logger
from app.modules.github.model import ParsedGitHubProfile
from app.modules.graph.agents.github_enrichment import enrich_github_project_with_llm
from app.modules.graph.agents.resume_enrichment import enrich_resume_with_llm
from app.modules.graph.employer_builder import (
    build_employer_nodes_and_edges,
    resolve_employer_enrichment,
)
from app.modules.graph.entity_builder import (
    capability_nodes_and_edges,
    project_node_and_edges,
)
from app.modules.graph.interface import GraphStore
from app.modules.graph.model import (
    EmployerEnrichmentResult,
    GitHubGraphEnrichment,
    GraphBuildResult,
    GraphEdge,
    GraphNode,
    ResumeGraphEnrichment,
)
from app.modules.graph.normalizer import build_candidate_id, build_project_id
from app.modules.graph.utils import persist_graph
from app.modules.llm.router import LLMRouter
from app.modules.resume.model import ParsedResume

logger = get_logger(__name__)


def build_candidate_graph(
    *,
    parsed_resume: ParsedResume,
    parsed_github: ParsedGitHubProfile,
    graph_store: GraphStore,
    github_enrichments: dict[str, GitHubGraphEnrichment] | None = None,
    resume_enrichment: ResumeGraphEnrichment | None = None,
    candidate_id: str | None = None,
) -> GraphBuildResult:
    active_candidate_id = candidate_id or build_candidate_id(
        github_url=parsed_resume.links.github,
        email=parsed_resume.links.emails[0] if parsed_resume.links.emails else None,
        name=parsed_resume.candidate_name,
    )

    nodes: list[GraphNode] = [
        GraphNode(
            node_id=active_candidate_id,
            label="Candidate",
            name=parsed_resume.candidate_name or active_candidate_id,
            properties={
                "github": parsed_resume.links.github,
                "summary": parsed_resume.summary,
            },
        )
    ]
    edges: list[GraphEdge] = []

    for project in parsed_github.projects:
        enrichment = (github_enrichments or {}).get(project.repo_link)
        project_nodes, project_edges = project_node_and_edges(
            active_candidate_id,
            project,
            enrichment=enrichment,
        )
        nodes.extend(project_nodes)
        edges.extend(project_edges)

    if resume_enrichment:
        _append_resume_enrichment(
            nodes,
            edges,
            parsed_resume=parsed_resume,
            resume_enrichment=resume_enrichment,
            candidate_id=active_candidate_id,
        )

    node_count, edge_count = persist_graph(graph_store, nodes, edges)
    logger.info(
        "Built candidate graph candidate=%s nodes=%s edges=%s",
        active_candidate_id,
        node_count,
        edge_count,
    )
    return GraphBuildResult(
        nodes_upserted=node_count,
        edges_upserted=edge_count,
        metadata={"candidate_id": active_candidate_id},
    )


def build_company_graph(
    *,
    company_records: list[dict[str, Any]],
    graph_store: GraphStore,
    enrichments: dict[str, EmployerEnrichmentResult] | None = None,
    llm_router: LLMRouter | None = None,
    max_records: int | None = None,
) -> GraphBuildResult:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    active_enrichments = enrichments or {}
    records = company_records[:max_records] if max_records else company_records

    for record in records:
        enrichment = resolve_employer_enrichment(
            record,
            enrichments=active_enrichments,
            llm_router=llm_router,
        )
        record_nodes, record_edges = build_employer_nodes_and_edges(record, enrichment)
        nodes.extend(record_nodes)
        edges.extend(record_edges)

    node_count, edge_count = persist_graph(graph_store, nodes, edges)
    logger.info("Built company graph records=%s nodes=%s edges=%s", len(records), node_count, edge_count)
    return GraphBuildResult(
        nodes_upserted=node_count,
        edges_upserted=edge_count,
        metadata={"records_processed": len(records)},
    )


def enrich_github_profile(
    parsed_github: ParsedGitHubProfile,
    *,
    llm_router: LLMRouter,
    max_projects: int | None = None,
) -> dict[str, GitHubGraphEnrichment]:
    projects = parsed_github.projects[:max_projects] if max_projects else parsed_github.projects
    return {
        project.repo_link: enrich_github_project_with_llm(project, llm_router=llm_router)
        for project in projects
    }


def enrich_resume_profile(
    parsed_resume: ParsedResume,
    parsed_github: ParsedGitHubProfile | None,
    *,
    llm_router: LLMRouter,
) -> ResumeGraphEnrichment:
    return enrich_resume_with_llm(parsed_resume, parsed_github, llm_router=llm_router)


def _append_resume_enrichment(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    *,
    parsed_resume: ParsedResume,
    resume_enrichment: ResumeGraphEnrichment,
    candidate_id: str,
) -> None:
    candidate_suffix = candidate_id.split(":", 1)[-1]

    for index, experience in enumerate(parsed_resume.experience):
        experience_id = f"experience:{candidate_suffix}:{index}"
        nodes.append(
            GraphNode(
                node_id=experience_id,
                label="Experience",
                name=experience.company_name or f"Experience {index + 1}",
                properties=experience.to_dict(),
            )
        )
        edges.append(GraphEdge(source_id=candidate_id, target_id=experience_id, relationship="HAS"))
        cap_nodes, cap_edges = capability_nodes_and_edges(
            experience_id,
            resume_enrichment.experience_capabilities.get(index, []),
        )
        nodes.extend(cap_nodes)
        edges.extend(cap_edges)

    for index, achievement in enumerate(parsed_resume.achievements):
        digest = hashlib.sha1(achievement.encode("utf-8")).hexdigest()[:10]
        achievement_id = f"achievement:{candidate_suffix}:{digest}"
        nodes.append(
            GraphNode(
                node_id=achievement_id,
                label="Achievement",
                name=achievement[:120],
                properties={"text": achievement},
            )
        )
        edges.append(GraphEdge(source_id=candidate_id, target_id=achievement_id, relationship="HAS"))
        cap_nodes, cap_edges = capability_nodes_and_edges(
            achievement_id,
            resume_enrichment.achievement_capabilities.get(index, []),
        )
        nodes.extend(cap_nodes)
        edges.extend(cap_edges)

    for index, repo_link in resume_enrichment.project_links.items():
        if not repo_link:
            continue
        edges.append(
            GraphEdge(
                source_id=candidate_id,
                target_id=build_project_id(repo_link),
                relationship="OWNS",
                properties={"source": "resume_project", "index": index},
            )
        )
