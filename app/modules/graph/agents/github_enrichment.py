from __future__ import annotations

import json

from app.core.logger import get_logger
from app.modules.github.model import ParsedGitHubProject
from app.modules.graph.model import GitHubGraphEnrichment
from app.modules.graph.prompt_builder import build_github_graph_user_prompt
from prompts.graph.github_enrichment import GITHUB_GRAPH_SYSTEM_PROMPT
from app.modules.graph.schemas import github_graph_enrichment_parser
from app.modules.llm.interface import LLMMessage, LLMRequest
from app.modules.llm.router import LLMRouter

logger = get_logger(__name__)


def enrich_github_project_with_llm(
    project: ParsedGitHubProject,
    *,
    llm_router: LLMRouter,
    max_tokens: int = 1200,
) -> GitHubGraphEnrichment:
    tech_stack = {
        "backend": project.tech_stack.backend,
        "frontend": project.tech_stack.frontend,
        "ai_ml": project.tech_stack.ai_ml,
    }
    user_prompt = build_github_graph_user_prompt(
        repo_name=project.repo_name,
        summary=project.summary,
        tech_stack=json.dumps(tech_stack, ensure_ascii=False),
        non_tech_tags=json.dumps(project.non_tech_tags, ensure_ascii=False),
        readme_text=project.raw_readme[:20000],
        format_instructions=github_graph_enrichment_parser.get_format_instructions(),
    )
    response = llm_router.generate(
        LLMRequest(
            messages=[
                LLMMessage(role="system", content=GITHUB_GRAPH_SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            temperature=0,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
    )
    parsed = _parse_github_enrichment(response.content)
    logger.debug("Enriched GitHub project repo=%s capabilities=%s", project.repo_name, len(parsed.capabilities))
    return parsed


def _parse_github_enrichment(content: str) -> GitHubGraphEnrichment:
    parsed = github_graph_enrichment_parser.parse(content)
    return GitHubGraphEnrichment(
        capabilities=parsed.capabilities,
        domains=parsed.domains,
        problems_solved=parsed.problems_solved,
        complexity=parsed.complexity,
        business_impact=parsed.business_impact,
        impact_signals=parsed.impact_signals,
    )
