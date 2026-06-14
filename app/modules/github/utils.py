from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from app.core.exceptions import InvalidGitHubError
from app.core.logger import get_logger
from app.core.string_normalizers import string_list, string_or_empty, string_or_none
from app.modules.github.config import GitHubParserConfig
from app.modules.github.model import (
    GitHubRepoReadme,
    GitHubTechStack,
    ParsedGitHubProfile,
    ParsedGitHubProject,
    github_project_parser,
)
from app.modules.github.prompt import GITHUB_SYSTEM_PROMPT, build_github_user_prompt
from app.modules.llm.interface import LLMMessage, LLMRequest

logger = get_logger(__name__)


def clean_readme_text(raw_text: str) -> str:
    text = raw_text.replace("\x00", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate_readme_text(raw_text: str, max_chars: int) -> str:
    cleaned_text = clean_readme_text(raw_text)

    if len(cleaned_text) <= max_chars:
        return cleaned_text

    return cleaned_text[:max_chars].rstrip()


def extract_github_username(github_url: str) -> str:
    normalized_url = github_url.strip()

    if not normalized_url:
        raise InvalidGitHubError("GitHub profile URL is required.")

    if not normalized_url.startswith(("http://", "https://")):
        normalized_url = f"https://{normalized_url.lstrip('/')}"

    parsed = urlparse(normalized_url)
    hostname = parsed.netloc.lower().removeprefix("www.")

    if hostname != "github.com":
        raise InvalidGitHubError("GitHub URL must point to github.com.")

    path_parts = [part for part in parsed.path.split("/") if part]

    if not path_parts:
        raise InvalidGitHubError("GitHub profile URL must include a username.")

    username = path_parts[0].strip()

    if not username or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", username):
        raise InvalidGitHubError("GitHub URL contains an invalid username.")

    return username


def build_github_profile_url(username: str) -> str:
    return f"https://github.com/{username}"


def build_github_project_structure_request(
    *,
    repo_name: str,
    cleaned_readme: str,
    config: GitHubParserConfig,
) -> LLMRequest:
    readme_text = cleaned_readme[: config.max_readme_chars]
    user_prompt = build_github_user_prompt(
        repo_name=repo_name,
        readme_text=readme_text,
        format_instructions=github_project_parser.get_format_instructions(),
    )

    return LLMRequest(
        messages=[
            LLMMessage(role="system", content=GITHUB_SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ],
        temperature=0,
        max_tokens=config.llm_max_tokens,
        response_format={"type": "json_object"},
    )


def parse_github_project_structure_response(content: str) -> dict[str, Any]:
    try:
        parsed_obj = github_project_parser.parse(content)
        return parsed_obj.model_dump()
    except Exception as error:
        logger.warning("Invalid GitHub project JSON from LLM: %s", error)
        raise InvalidGitHubError(
            f"LLM returned invalid GitHub project JSON: {error}"
        ) from error


def build_parsed_github_project_from_structure(
    *,
    repo_name: str,
    repo_link: str,
    raw_readme: str,
    structure: dict[str, Any],
) -> ParsedGitHubProject:
    tech_stack_value = structure.get("tech_stack")

    if isinstance(tech_stack_value, dict):
        tech_stack = GitHubTechStack(
            backend=string_list(tech_stack_value.get("backend")),
            frontend=string_list(tech_stack_value.get("frontend")),
            ai_ml=string_list(tech_stack_value.get("ai_ml")),
        )
    else:
        tech_stack = GitHubTechStack()

    return ParsedGitHubProject(
        repo_name=repo_name,
        repo_link=repo_link,
        deployed_link=string_or_none(structure.get("deployed_link")),
        summary=string_or_empty(structure.get("summary")),
        tech_stack=tech_stack,
        non_tech_tags=string_list(structure.get("non_tech_tags")),
        raw_readme=raw_readme,
    )


def build_readme_only_github_project(repo: GitHubRepoReadme) -> ParsedGitHubProject:
    return ParsedGitHubProject(
        repo_name=repo.repo_name,
        repo_link=repo.repo_link,
        deployed_link=None,
        summary="",
        tech_stack=GitHubTechStack(),
        non_tech_tags=[],
        raw_readme=repo.raw_readme,
    )


def build_parsed_github_profile(
    *,
    github_username: str,
    github_url: str,
    projects: list[ParsedGitHubProject],
    metadata: dict[str, Any] | None = None,
) -> ParsedGitHubProfile:
    return ParsedGitHubProfile(
        github_username=github_username,
        github_url=github_url,
        projects=projects,
        metadata=metadata or {},
    )
