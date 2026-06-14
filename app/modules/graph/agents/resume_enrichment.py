from __future__ import annotations

import json

from app.core.logger import get_logger
from app.modules.github.model import ParsedGitHubProfile
from app.modules.graph.model import ResumeGraphEnrichment
from app.modules.graph.normalizer import links_match_project
from app.modules.graph.prompt_builder import build_resume_graph_user_prompt
from prompts.graph.resume_enrichment import RESUME_GRAPH_SYSTEM_PROMPT
from app.modules.graph.schemas import resume_graph_enrichment_parser
from app.modules.llm.interface import LLMMessage, LLMRequest
from app.modules.llm.router import LLMRouter
from app.modules.resume.model import ParsedResume

logger = get_logger(__name__)


def enrich_resume_with_llm(
    parsed_resume: ParsedResume,
    parsed_github: ParsedGitHubProfile | None,
    *,
    llm_router: LLMRouter,
    max_tokens: int = 1500,
) -> ResumeGraphEnrichment:
    github_repos = []
    if parsed_github:
        github_repos = [project.repo_link for project in parsed_github.projects]

    user_prompt = build_resume_graph_user_prompt(
        candidate_name=parsed_resume.candidate_name or "",
        skills=json.dumps(parsed_resume.skills, ensure_ascii=False),
        experience=json.dumps([item.to_dict() for item in parsed_resume.experience], ensure_ascii=False),
        achievements=json.dumps(parsed_resume.achievements, ensure_ascii=False),
        projects=json.dumps([item.to_dict() for item in parsed_resume.projects], ensure_ascii=False),
        github_repos=json.dumps(github_repos, ensure_ascii=False),
        format_instructions=resume_graph_enrichment_parser.get_format_instructions(),
    )
    response = llm_router.generate(
        LLMRequest(
            messages=[
                LLMMessage(role="system", content=RESUME_GRAPH_SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            temperature=0,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
    )
    parsed = resume_graph_enrichment_parser.parse(response.content)

    project_links: dict[int, str | None] = {}
    for index, project in enumerate(parsed_resume.projects):
        matched = None
        if parsed_github:
            for github_project in parsed_github.projects:
                if links_match_project(project.link, github_project.repo_link):
                    matched = github_project.repo_link
                    break
        project_links[index] = matched

    for item in parsed.project_links:
        if item.matched_repo_link:
            project_links[item.index] = item.matched_repo_link

    experience_capabilities = {
        item.index: item.capabilities for item in parsed.experience_capabilities
    }
    achievement_capabilities = {
        item.index: item.capabilities for item in parsed.achievement_capabilities
    }

    logger.debug(
        "Enriched resume candidate=%s experiences=%s achievements=%s",
        parsed_resume.candidate_name,
        len(experience_capabilities),
        len(achievement_capabilities),
    )

    return ResumeGraphEnrichment(
        experience_capabilities=experience_capabilities,
        achievement_capabilities=achievement_capabilities,
        project_links=project_links,
        skill_technologies=parsed.inferred_skill_technologies or parsed_resume.skills,
    )
