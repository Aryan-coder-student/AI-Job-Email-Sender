from __future__ import annotations

from typing import Any

from app.modules.graph.agents.employer_enrichment import enrich_employer_with_llm
from app.modules.graph.entity_builder import (
    capability_nodes_and_edges,
    domain_nodes_and_edges,
    technology_requirement_edges,
)
from app.modules.graph.model import (
    EmployerEnrichmentInput,
    EmployerEnrichmentResult,
    GraphEdge,
    GraphNode,
)
from app.modules.graph.normalizer import build_company_id, build_job_id, build_role_id
from app.modules.llm.router import LLMRouter


def build_employer_nodes_and_edges(
    record: dict[str, Any],
    enrichment: EmployerEnrichmentResult | None,
) -> tuple[list[GraphNode], list[GraphEdge]]:
    company_name = str(record.get("company_name") or "").strip()
    if not company_name:
        return [], []

    company_id = build_company_id(
        company_name=company_name,
        company_url=record.get("company_url"),
    )
    nodes: list[GraphNode] = [
        GraphNode(
            node_id=company_id,
            label="Company",
            name=company_name,
            properties={
                "company_url": record.get("company_url"),
                "company_description": record.get("company_description"),
            },
        )
    ]
    edges: list[GraphEdge] = []

    role = record.get("role")
    role_id = None
    if role:
        role_id = build_role_id(str(role))
        nodes.append(GraphNode(node_id=role_id, label="Role", name=str(role)))

    job_id = build_job_id(
        company_id=company_id,
        job_url=record.get("job_url"),
        source_row=record.get("source_row"),
    )
    nodes.append(
        GraphNode(
            node_id=job_id,
            label="JobOpening",
            name=f"{company_name} opening",
            properties={
                "job_url": record.get("job_url"),
                "company_description": record.get("company_description"),
                "job_description": record.get("job_description"),
                "role": role,
                "hr_email": record.get("hr_email"),
            },
        )
    )
    edges.append(GraphEdge(source_id=job_id, target_id=company_id, relationship="AT"))
    if role_id:
        edges.append(GraphEdge(source_id=job_id, target_id=role_id, relationship="FOR"))

    if enrichment is None:
        return nodes, edges

    domain_nodes, domain_edges = domain_nodes_and_edges(
        company_id,
        enrichment.company_domains,
        relationship="OPERATES_IN",
    )
    nodes.extend(domain_nodes)
    edges.extend(domain_edges)

    company_caps, company_cap_edges = capability_nodes_and_edges(
        company_id,
        enrichment.company_looked_for_capabilities,
        relationship="LOOKS_FOR",
    )
    nodes.extend(company_caps)
    edges.extend(company_cap_edges)

    company_tech_nodes, company_tech_edges = technology_requirement_edges(
        company_id,
        enrichment.company_looked_for_technologies,
        relationship="LOOKS_FOR",
    )
    nodes.extend(company_tech_nodes)
    edges.extend(company_tech_edges)

    job_caps, job_cap_edges = capability_nodes_and_edges(
        job_id,
        enrichment.job_required_capabilities,
        relationship="REQUIRES",
    )
    nodes.extend(job_caps)
    edges.extend(job_cap_edges)

    job_tech_nodes, job_tech_edges = technology_requirement_edges(
        job_id,
        enrichment.job_required_technologies,
        relationship="REQUIRES",
    )
    nodes.extend(job_tech_nodes)
    edges.extend(job_tech_edges)

    if role_id:
        role_caps, role_cap_edges = capability_nodes_and_edges(
            role_id,
            enrichment.job_required_capabilities,
            relationship="REQUIRES",
        )
        nodes.extend(role_caps)
        edges.extend(role_cap_edges)

    return nodes, edges


def resolve_employer_enrichment(
    record: dict[str, Any],
    *,
    enrichments: dict[str, EmployerEnrichmentResult],
    llm_router: LLMRouter | None,
) -> EmployerEnrichmentResult | None:
    company_name = str(record.get("company_name") or "").strip()
    if not company_name:
        return None

    enrichment_key = company_name.lower()
    cached = enrichments.get(enrichment_key)
    if cached is not None:
        return cached
    if llm_router is None:
        return None

    enrichment = enrich_employer_with_llm(
        EmployerEnrichmentInput(
            company_name=company_name,
            company_description=record.get("company_description"),
            job_description=record.get("job_description"),
            role=record.get("role"),
        ),
        llm_router=llm_router,
    )
    enrichments[enrichment_key] = enrichment
    return enrichment
