from __future__ import annotations

from app.modules.github.model import ParsedGitHubProject
from app.modules.graph.model import (
    GitHubGraphEnrichment,
    GraphEdge,
    GraphNode,
    RelationshipType,
)
from app.modules.graph.normalizer import (
    build_capability_id,
    build_domain_id,
    build_ontology_term_id,
    build_project_id,
    build_technology_id,
    normalize_capability,
    normalize_domain,
    normalize_technology,
)
from app.modules.graph.ontology import load_ontology


def technology_nodes_and_edges(
    project_id: str,
    technologies: list[str],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    ontology = load_ontology()

    for raw_label in technologies:
        if not raw_label.strip():
            continue
        technology_id = build_technology_id(raw_label)
        canonical = normalize_technology(raw_label)
        nodes.append(
            GraphNode(
                node_id=technology_id,
                label="Technology",
                name=raw_label.strip(),
                properties={"slug": canonical},
            )
        )
        edges.append(
            GraphEdge(
                source_id=project_id,
                target_id=technology_id,
                relationship="USES",
                properties={"raw_label": raw_label.strip()},
            )
        )

        category = ontology.technology_aliases.get(raw_label.strip().lower())
        if category:
            term_id = build_ontology_term_id("technology", category)
            nodes.append(
                GraphNode(
                    node_id=term_id,
                    label="OntologyTerm",
                    name=category,
                    properties={"category": "technology"},
                )
            )
            edges.append(
                GraphEdge(
                    source_id=technology_id,
                    target_id=term_id,
                    relationship="IS_A",
                )
            )

    return nodes, edges


def capability_nodes_and_edges(
    source_id: str,
    capabilities: list[str],
    *,
    relationship: RelationshipType = "DEMONSTRATES",
) -> tuple[list[GraphNode], list[GraphEdge]]:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    ontology = load_ontology()

    for raw_label in capabilities:
        if not raw_label.strip():
            continue
        capability_id = build_capability_id(raw_label)
        canonical = normalize_capability(raw_label)
        nodes.append(
            GraphNode(
                node_id=capability_id,
                label="Capability",
                name=raw_label.strip(),
                properties={"slug": canonical},
            )
        )
        edges.append(
            GraphEdge(
                source_id=source_id,
                target_id=capability_id,
                relationship=relationship,
                properties={"raw_label": raw_label.strip()},
            )
        )

        category = ontology.capability_aliases.get(raw_label.strip().lower())
        if category:
            term_id = build_ontology_term_id("capability", category)
            nodes.append(
                GraphNode(
                    node_id=term_id,
                    label="OntologyTerm",
                    name=category,
                    properties={"category": "capability"},
                )
            )
            edges.append(
                GraphEdge(
                    source_id=capability_id,
                    target_id=term_id,
                    relationship="IS_A",
                )
            )

    return nodes, edges


def domain_nodes_and_edges(
    source_id: str,
    domains: list[str],
    *,
    relationship: str = "BELONGS_TO",
) -> tuple[list[GraphNode], list[GraphEdge]]:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    for raw_label in domains:
        if not raw_label.strip():
            continue
        domain_id = build_domain_id(raw_label)
        nodes.append(
            GraphNode(
                node_id=domain_id,
                label="Domain",
                name=raw_label.strip(),
                properties={"slug": normalize_domain(raw_label)},
            )
        )
        edges.append(
            GraphEdge(
                source_id=source_id,
                target_id=domain_id,
                relationship=relationship,
                properties={"raw_label": raw_label.strip()},
            )
        )

    return nodes, edges


def technology_requirement_edges(
    source_id: str,
    technologies: list[str],
    *,
    relationship: RelationshipType,
) -> tuple[list[GraphNode], list[GraphEdge]]:
    nodes, uses_edges = technology_nodes_and_edges(source_id, technologies)
    edges = [
        GraphEdge(
            source_id=source_id,
            target_id=edge.target_id,
            relationship=relationship,
            properties=edge.properties,
        )
        for edge in uses_edges
    ]
    return nodes, edges


def project_node_and_edges(
    candidate_id: str,
    project: ParsedGitHubProject,
    enrichment: GitHubGraphEnrichment | None = None,
) -> tuple[list[GraphNode], list[GraphEdge]]:
    project_id = build_project_id(project.repo_link)
    nodes = [
        GraphNode(
            node_id=project_id,
            label="Project",
            name=project.repo_name,
            properties={
                "repo_link": project.repo_link,
                "summary": project.summary,
                "deployed_link": project.deployed_link,
            },
        )
    ]
    edges = [
        GraphEdge(
            source_id=candidate_id,
            target_id=project_id,
            relationship="OWNS",
        )
    ]

    technologies = [
        *project.tech_stack.backend,
        *project.tech_stack.frontend,
        *project.tech_stack.ai_ml,
    ]
    tech_nodes, tech_edges = technology_nodes_and_edges(project_id, technologies)
    nodes.extend(tech_nodes)
    edges.extend(tech_edges)

    domains = list(project.non_tech_tags)
    capabilities: list[str] = []
    if enrichment:
        domains.extend(enrichment.domains)
        capabilities.extend(enrichment.capabilities)

    domain_nodes, domain_edges = domain_nodes_and_edges(project_id, domains)
    nodes.extend(domain_nodes)
    edges.extend(domain_edges)

    capability_nodes, capability_edges = capability_nodes_and_edges(project_id, capabilities)
    nodes.extend(capability_nodes)
    edges.extend(capability_edges)

    return nodes, edges
