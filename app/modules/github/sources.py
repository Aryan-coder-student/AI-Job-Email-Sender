from __future__ import annotations

from github import Github
from github.GithubException import GithubException, UnknownObjectException

from app.core.exceptions import InvalidGitHubError
from app.modules.github.config import GitHubParserConfig
from app.modules.github.model import GitHubRepoReadme
from app.modules.github.utils import clean_readme_text


def fetch_user_repos_with_readmes(
    username: str,
    config: GitHubParserConfig,
) -> tuple[list[GitHubRepoReadme], list[dict[str, str]]]:
    client = Github(login_or_token=config.github_token)
    user = _get_github_user(client, username)

    repos_with_readmes: list[GitHubRepoReadme] = []
    skipped_repos: list[dict[str, str]] = []
    repos_fetched = 0

    try:
        for repo in user.get_repos():
            if repos_fetched >= config.max_repos:
                break

            repos_fetched += 1
            repo_result = _fetch_repo_readme(repo, config.min_readme_chars)

            if isinstance(repo_result, GitHubRepoReadme):
                repos_with_readmes.append(repo_result)
                continue

            skipped_repos.append({"name": repo.name, "reason": repo_result})
    except GithubException as error:
        raise InvalidGitHubError(
            f"Failed to fetch repositories for {username}: {error}"
        ) from error

    return repos_with_readmes, skipped_repos


def _get_github_user(client: Github, username: str):
    try:
        return client.get_user(username)
    except UnknownObjectException as error:
        raise InvalidGitHubError(f"GitHub user not found: {username}") from error
    except GithubException as error:
        raise InvalidGitHubError(f"Failed to fetch GitHub user {username}: {error}") from error


def _fetch_repo_readme(repo, min_readme_chars: int) -> GitHubRepoReadme | str:
    try:
        readme = repo.get_readme()
    except UnknownObjectException:
        return "no_readme"

    raw_text = _decode_readme_content(readme.decoded_content)
    cleaned_text = clean_readme_text(raw_text)

    if len(cleaned_text) < min_readme_chars:
        return "empty_readme"

    return GitHubRepoReadme(
        repo_name=repo.name,
        repo_link=repo.html_url,
        raw_readme=cleaned_text,
    )


def _decode_readme_content(content: bytes) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue

    return content.decode("utf-8", errors="replace")
