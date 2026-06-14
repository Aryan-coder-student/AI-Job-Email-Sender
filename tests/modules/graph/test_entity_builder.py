from __future__ import annotations

from app.modules.github.model import GitHubTechStack, ParsedGitHubProject
from app.modules.graph.entity_builder import project_node_and_edges
from app.modules.graph.model import GitHubGraphEnrichment


def test_project_node_and_edges_create_technology_and_capability_nodes() -> None:
    project = ParsedGitHubProject(
        repo_name="AI-Job-Email-Sender",
        repo_link="https://github.com/user/AI-Job-Email-Sender",
        deployed_link=None,
        summary="Email automation project",
        tech_stack=GitHubTechStack(backend=["FastAPI"], frontend=[], ai_ml=["LangChain"]),
        non_tech_tags=["recruitment"],
        raw_readme="README",
    )
    enrichment = GitHubGraphEnrichment(
        capabilities=["Workflow Automation"],
        domains=["Recruitment"],
    )
    nodes, edges = project_node_and_edges(
        "candidate:test",
        project,
        enrichment=enrichment,
    )
    labels = {node.label for node in nodes}
    relationships = {edge.relationship for edge in edges}
    assert "Project" in labels
    assert "Technology" in labels
    assert "Capability" in labels
    assert "Domain" in labels
    assert "OWNS" in relationships
    assert "USES" in relationships
    assert "DEMONSTRATES" in relationships
