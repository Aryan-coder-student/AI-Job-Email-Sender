from __future__ import annotations

from prompts.graph.employer_enrichment import EMPLOYER_GRAPH_USER_PROMPT
from prompts.graph.github_enrichment import GITHUB_GRAPH_USER_PROMPT
from prompts.graph.resume_enrichment import RESUME_GRAPH_USER_PROMPT


def build_resume_graph_user_prompt(
    *,
    candidate_name: str,
    skills: str,
    experience: str,
    achievements: str,
    projects: str,
    github_repos: str,
    format_instructions: str,
) -> str:
    return RESUME_GRAPH_USER_PROMPT.format(
        candidate_name=candidate_name or "Unknown",
        skills=skills,
        experience=experience,
        achievements=achievements,
        projects=projects,
        github_repos=github_repos,
        format_instructions=format_instructions,
    )


def build_employer_graph_user_prompt(
    *,
    company_name: str,
    role: str,
    company_description: str,
    job_description: str,
    input_mode: str,
    format_instructions: str,
) -> str:
    return EMPLOYER_GRAPH_USER_PROMPT.format(
        company_name=company_name,
        role=role or "N/A",
        company_description=company_description or "N/A",
        job_description=job_description or "N/A",
        input_mode=input_mode,
        format_instructions=format_instructions,
    )


def build_github_graph_user_prompt(
    *,
    repo_name: str,
    summary: str,
    tech_stack: str,
    non_tech_tags: str,
    readme_text: str,
    format_instructions: str,
) -> str:
    return GITHUB_GRAPH_USER_PROMPT.format(
        repo_name=repo_name,
        summary=summary,
        tech_stack=tech_stack,
        non_tech_tags=non_tech_tags,
        readme_text=readme_text,
        format_instructions=format_instructions,
    )
