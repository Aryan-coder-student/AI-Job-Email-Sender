from __future__ import annotations

from app.modules.graph.normalizer import (
    build_candidate_id,
    build_company_id,
    links_match_project,
    normalize_capability,
    normalize_technology,
    slugify,
)


def test_slugify_normalizes_text() -> None:
    assert slugify("LangChain") == "langchain"


def test_normalize_technology_uses_ontology_alias() -> None:
    assert normalize_technology("LangChain") == "agent_framework"


def test_normalize_capability_uses_ontology_alias() -> None:
    assert normalize_capability("RAG") == "rag"


def test_build_candidate_id_from_github() -> None:
    assert build_candidate_id(github_url="https://github.com/Aryan-coder-student") == "candidate:aryan_coder_student"


def test_build_company_id_from_url() -> None:
    company_id = build_company_id(company_name="Acme", company_url="https://acme.com")
    assert company_id.startswith("company:")


def test_links_match_project_by_repo_slug() -> None:
    assert links_match_project(
        "https://github.com/user/AI-Job-Email-Sender",
        "https://github.com/user/AI-Job-Email-Sender",
    )
