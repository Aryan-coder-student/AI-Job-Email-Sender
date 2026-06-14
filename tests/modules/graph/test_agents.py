from __future__ import annotations

import json
from unittest.mock import MagicMock

from app.modules.github.model import GitHubTechStack, ParsedGitHubProject
from app.modules.graph.agents.employer_enrichment import enrich_employer_with_llm
from app.modules.graph.agents.github_enrichment import enrich_github_project_with_llm
from app.modules.graph.model import EmployerEnrichmentInput
from app.modules.llm.interface import LLMResponse


def test_enrich_github_project_with_llm_parses_capabilities() -> None:
    project = ParsedGitHubProject(
        repo_name="AI-Job-Email-Sender",
        repo_link="https://github.com/user/AI-Job-Email-Sender",
        deployed_link=None,
        summary="Email automation",
        tech_stack=GitHubTechStack(backend=["python"], frontend=[], ai_ml=["LangChain"]),
        non_tech_tags=["recruitment"],
        raw_readme="Uses LangChain for workflow automation.",
    )
    router = MagicMock()
    router.generate.return_value = LLMResponse(
        content=json.dumps(
            {
                "capabilities": ["Workflow Automation"],
                "domains": ["Recruitment"],
                "problems_solved": ["Automated outreach"],
                "complexity": "medium",
                "business_impact": "Faster applications",
                "impact_signals": ["deployed"],
            }
        ),
        provider="groq",
        model="test",
    )
    enrichment = enrich_github_project_with_llm(project, llm_router=router)
    assert "Workflow Automation" in enrichment.capabilities
    assert "Recruitment" in enrichment.domains


def test_enrich_employer_with_llm_supports_company_only_mode() -> None:
    router = MagicMock()
    router.generate.return_value = LLMResponse(
        content=json.dumps(
            {
                "company_domains": ["Web Development"],
                "company_looked_for_capabilities": ["Workflow Automation"],
                "company_looked_for_technologies": ["React"],
                "job_required_capabilities": [],
                "job_required_technologies": [],
                "industry": "Software",
                "enrichment_source": "company",
            }
        ),
        provider="groq",
        model="test",
    )
    result = enrich_employer_with_llm(
        EmployerEnrichmentInput(
            company_name="100Starlings",
            company_description="Custom web/mobile dev cooperative",
        ),
        llm_router=router,
    )
    assert result.enrichment_source == "company"
    assert result.company_looked_for_capabilities
