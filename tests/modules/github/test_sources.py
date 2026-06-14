from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import InvalidGitHubError
from app.modules.github.config import GitHubParserConfig
from app.modules.github.sources import fetch_user_repos_with_readmes
from github.GithubException import UnknownObjectException


class FakeReadme:
    def __init__(self, content: bytes) -> None:
        self.decoded_content = content


class FakeRepo:
    def __init__(self, name: str, html_url: str, readme_content: bytes | None) -> None:
        self.name = name
        self.html_url = html_url
        self._readme_content = readme_content

    def get_readme(self) -> FakeReadme:
        if self._readme_content is None:
            raise UnknownObjectException(404, {"message": "Not Found"}, None)

        return FakeReadme(self._readme_content)


class FakeUser:
    def __init__(self, repos: list[FakeRepo]) -> None:
        self._repos = repos

    def get_repos(self) -> list[FakeRepo]:
        return self._repos


def test_fetch_user_repos_with_readmes_skips_missing_and_empty_readmes() -> None:
    repos = [
        FakeRepo("filled", "https://github.com/aryan/filled", b"# Project\n" + b"x" * 100),
        FakeRepo("empty", "https://github.com/aryan/empty", b"# Title"),
        FakeRepo("missing", "https://github.com/aryan/missing", None),
    ]
    fake_user = FakeUser(repos)
    fake_client = MagicMock()
    fake_client.get_user.return_value = fake_user

    with patch("app.modules.github.sources.Github", return_value=fake_client):
        repos_with_readmes, skipped = fetch_user_repos_with_readmes(
            "aryan",
            GitHubParserConfig(min_readme_chars=80),
        )

    assert len(repos_with_readmes) == 1
    assert repos_with_readmes[0].repo_name == "filled"
    assert skipped == [
        {"name": "empty", "reason": "empty_readme"},
        {"name": "missing", "reason": "no_readme"},
    ]


def test_fetch_user_repos_with_readmes_raises_for_missing_user() -> None:
    fake_client = MagicMock()
    fake_client.get_user.side_effect = UnknownObjectException(
        404,
        {"message": "Not Found"},
        None,
    )

    with patch("app.modules.github.sources.Github", return_value=fake_client):
        with pytest.raises(InvalidGitHubError, match="GitHub user not found"):
            fetch_user_repos_with_readmes("missing-user", GitHubParserConfig())
