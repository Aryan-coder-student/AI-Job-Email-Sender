from __future__ import annotations

from app.modules.github.model import (
    GitHubTechStack,
    ParsedGitHubProfile,
    ParsedGitHubProject,
)
from app.modules.graph.builder import build_candidate_graph
from app.modules.resume.model import ParsedResume, ResumeLinks


class FakeGraphStore:
    name = "fake"

    def upsert_nodes(self, nodes):
        self.nodes = nodes
        return len(nodes)

    def upsert_edges(self, edges):
        self.edges = edges
        return len(edges)

    def clear(self) -> None:
        pass

    def match_projects_for_employer(self, employer, *, candidate_id, limit=10):
        return [], []

    def close(self) -> None:
        pass


def test_build_candidate_graph_upserts_project_nodes() -> None:
    store = FakeGraphStore()
    parsed_resume = ParsedResume(
        filename="resume.pdf",
        file_extension=".pdf",
        raw_text="text",
        candidate_name="Aryan",
        summary="",
        skills=[],
        experience=[],
        projects=[],
        courses=[],
        certifications=[],
        achievements=[],
        research=[],
        education=[],
        links=ResumeLinks(github="https://github.com/Aryan-coder-student"),
    )
    parsed_github = ParsedGitHubProfile(
        github_username="Aryan-coder-student",
        github_url="https://github.com/Aryan-coder-student",
        projects=[
            ParsedGitHubProject(
                repo_name="AI-Job-Email-Sender",
                repo_link="https://github.com/Aryan-coder-student/AI-Job-Email-Sender",
                deployed_link=None,
                summary="summary",
                tech_stack=GitHubTechStack(backend=["python"], frontend=[], ai_ml=[]),
                non_tech_tags=["recruitment"],
                raw_readme="readme",
            )
        ],
    )
    result = build_candidate_graph(
        parsed_resume=parsed_resume,
        parsed_github=parsed_github,
        graph_store=store,
        candidate_id="candidate:aryan",
    )
    assert result.nodes_upserted > 0
    assert result.edges_upserted > 0
    assert any(node.label == "Project" for node in store.nodes)
