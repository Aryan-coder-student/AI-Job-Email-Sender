from __future__ import annotations

from typing import Any

from app.core.exceptions import InvalidGitHubError


def validate_github_parser_config(config: Any) -> None:
    if config.max_repos < 1:
        raise ValueError("max_repos must be at least 1.")

    if config.min_readme_chars < 1:
        raise ValueError("min_readme_chars must be at least 1.")

    if config.max_readme_chars < 1:
        raise ValueError("max_readme_chars must be at least 1.")

    if config.llm_max_tokens < 1:
        raise ValueError("llm_max_tokens must be at least 1.")

    if config.llm_max_workers < 1:
        raise ValueError("llm_max_workers must be at least 1.")


def validate_github_url(github_url: str | None) -> str:
    if not github_url or not github_url.strip():
        raise InvalidGitHubError("GitHub profile URL is required.")

    return github_url.strip()
