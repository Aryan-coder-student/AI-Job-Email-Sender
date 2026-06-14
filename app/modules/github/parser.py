from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any

from app.core.exceptions import InvalidGitHubError
from app.core.logger import get_logger
from app.modules.github.agent import extract_project_structure_with_llm
from app.modules.github.config import GitHubParserConfig
from app.modules.github.model import GitHubRepoReadme, ParsedGitHubProfile, ParsedGitHubProject
from app.modules.github.sources import fetch_user_repos_with_readmes
from app.modules.github.utils import (
    build_github_profile_url,
    build_parsed_github_profile,
    build_readme_only_github_project,
    extract_github_username,
)
from app.modules.github.validator import validate_github_url
from app.modules.resume.model import ParsedResume

if TYPE_CHECKING:
    from app.modules.llm.router import LLMRouter

logger = get_logger(__name__)


def parse_github_from_resume(
    parsed_resume: ParsedResume,
    *,
    config: GitHubParserConfig | None = None,
    llm_router: LLMRouter | None = None,
) -> ParsedGitHubProfile:
    github_url = validate_github_url(parsed_resume.links.github)
    return parse_github_profile(
        github_url,
        config=config,
        llm_router=llm_router,
    )


def parse_github_profile(
    github_url: str,
    *,
    config: GitHubParserConfig | None = None,
    llm_router: LLMRouter | None = None,
) -> ParsedGitHubProfile:
    active_config = config or GitHubParserConfig()
    active_config.validate()

    username = extract_github_username(validate_github_url(github_url))
    logger.info("Parsing GitHub profile for user=%s", username)

    repos_with_readmes, skipped_repos = fetch_user_repos_with_readmes(
        username,
        active_config,
    )
    projects, metadata = _build_projects_and_metadata(
        repos_with_readmes,
        skipped_repos,
        llm_router=llm_router,
        config=active_config,
    )

    if not projects and not skipped_repos:
        logger.warning("No repositories found for GitHub user=%s", username)
        raise InvalidGitHubError(
            f"No repositories with readable READMEs were found for {username}."
        )

    logger.info(
        "Parsed GitHub profile user=%s projects=%s skipped=%s mode=%s",
        username,
        len(projects),
        len(skipped_repos),
        metadata.get("structured_by") or "readme_only",
    )

    return build_parsed_github_profile(
        github_username=username,
        github_url=build_github_profile_url(username),
        projects=projects,
        metadata=metadata,
    )


def _build_projects_and_metadata(
    repos_with_readmes: list[GitHubRepoReadme],
    skipped_repos: list[dict[str, str]],
    *,
    llm_router: LLMRouter | None,
    config: GitHubParserConfig,
) -> tuple[list[ParsedGitHubProject], dict[str, Any]]:
    if llm_router is None:
        logger.debug("Skipping LLM extraction for %s README repositories", len(repos_with_readmes))
        projects = [build_readme_only_github_project(repo) for repo in repos_with_readmes]
        return projects, _build_fetch_metadata(
            repos_with_readmes,
            skipped_repos,
            structured_by=None,
        )

    projects, llm_runs = _extract_projects_with_llm(
        repos_with_readmes,
        llm_router=llm_router,
        config=config,
    )
    metadata = _build_fetch_metadata(
        repos_with_readmes,
        skipped_repos,
        structured_by="llm",
    )
    metadata["llm_runs"] = llm_runs
    metadata["llm_max_workers"] = config.llm_max_workers
    return projects, metadata


def _extract_projects_with_llm(
    repos_with_readmes: list[GitHubRepoReadme],
    *,
    llm_router: LLMRouter,
    config: GitHubParserConfig,
) -> tuple[list[ParsedGitHubProject], list[dict[str, Any]]]:
    if len(repos_with_readmes) <= 1 or config.llm_max_workers == 1:
        logger.debug(
            "Extracting GitHub README structures sequentially for %s repositories",
            len(repos_with_readmes),
        )
        return _extract_projects_with_llm_sequential(
            repos_with_readmes,
            llm_router=llm_router,
            config=config,
        )

    indexed_results: list[tuple[int, ParsedGitHubProject, dict[str, Any]]] = []
    logger.info(
        "Extracting GitHub README structures in parallel repos=%s workers=%s",
        len(repos_with_readmes),
        config.llm_max_workers,
    )

    with ThreadPoolExecutor(max_workers=config.llm_max_workers) as executor:
        futures = {
            executor.submit(
                extract_project_structure_with_llm,
                repo=repo,
                llm_router=llm_router,
                config=config,
            ): index
            for index, repo in enumerate(repos_with_readmes)
        }

        for future in as_completed(futures):
            index = futures[future]
            project, metadata = future.result()
            indexed_results.append((index, project, metadata))

    indexed_results.sort(key=lambda item: item[0])
    projects = [item[1] for item in indexed_results]
    llm_runs = [item[2] for item in indexed_results]
    return projects, llm_runs


def _extract_projects_with_llm_sequential(
    repos_with_readmes: list[GitHubRepoReadme],
    *,
    llm_router: LLMRouter,
    config: GitHubParserConfig,
) -> tuple[list[ParsedGitHubProject], list[dict[str, Any]]]:
    projects: list[ParsedGitHubProject] = []
    llm_runs: list[dict[str, Any]] = []

    for repo in repos_with_readmes:
        project, metadata = extract_project_structure_with_llm(
            repo=repo,
            llm_router=llm_router,
            config=config,
        )
        projects.append(project)
        llm_runs.append(metadata)

    return projects, llm_runs


def _build_fetch_metadata(
    repos_with_readmes: list[GitHubRepoReadme],
    skipped_repos: list[dict[str, str]],
    *,
    structured_by: str | None,
) -> dict[str, Any]:
    return {
        "repos_fetched": len(repos_with_readmes) + len(skipped_repos),
        "repos_parsed": len(repos_with_readmes),
        "skipped_repos": skipped_repos,
        "structured_by": structured_by,
    }
