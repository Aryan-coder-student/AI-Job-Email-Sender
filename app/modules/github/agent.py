from __future__ import annotations

from typing import Any

from app.modules.github.config import GitHubParserConfig
from app.modules.github.model import ParsedGitHubProject
from app.modules.github.utils import (
    GitHubRepoReadme,
    build_github_project_structure_request,
    build_parsed_github_project_from_structure,
    parse_github_project_structure_response,
    truncate_readme_text,
)
from app.modules.llm.router import LLMRouter


def extract_project_structure_with_llm(
    *,
    repo: GitHubRepoReadme,
    llm_router: LLMRouter,
    config: GitHubParserConfig,
) -> tuple[ParsedGitHubProject, dict[str, Any]]:
    cleaned_readme = truncate_readme_text(repo.raw_readme, config.max_readme_chars)
    response = llm_router.generate(
        build_github_project_structure_request(
            repo_name=repo.repo_name,
            cleaned_readme=cleaned_readme,
            config=config,
        )
    )
    structure = parse_github_project_structure_response(response.content)

    project = build_parsed_github_project_from_structure(
        repo_name=repo.repo_name,
        repo_link=repo.repo_link,
        raw_readme=cleaned_readme,
        structure=structure,
    )
    metadata = {
        "repo_name": repo.repo_name,
        "llm_provider": response.provider,
        "llm_model": response.model,
    }

    return project, metadata
