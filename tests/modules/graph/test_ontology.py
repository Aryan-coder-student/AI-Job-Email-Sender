from __future__ import annotations

from app.modules.graph.ontology import load_ontology


def test_load_ontology_contains_agent_framework_aliases() -> None:
    ontology = load_ontology()
    assert ontology.technology_aliases["langchain"] == "agent_framework"
    assert "LangChain" in ontology.technology_categories["agent_framework"]
