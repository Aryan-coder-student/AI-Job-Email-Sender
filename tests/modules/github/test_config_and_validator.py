from __future__ import annotations

import pytest

from app.core.exceptions import InvalidGitHubError
from app.modules.github.config import GitHubParserConfig
from app.modules.github.validator import validate_github_parser_config, validate_github_url


def test_github_parser_config_defaults() -> None:
    config = GitHubParserConfig()

    assert config.max_repos == 100
    assert config.min_readme_chars == 80
    assert config.max_readme_chars == 20000
    assert config.llm_max_tokens == 1500
    assert config.llm_max_workers == 5


def test_validate_github_url_accepts_non_empty_value() -> None:
    assert validate_github_url(" https://github.com/aryan ") == "https://github.com/aryan"


def test_validate_github_url_rejects_missing_value() -> None:
    with pytest.raises(InvalidGitHubError, match="required"):
        validate_github_url(None)


def test_github_parser_config_validate_calls_validator() -> None:
    GitHubParserConfig().validate()

    with pytest.raises(ValueError):
        GitHubParserConfig(max_repos=0).validate()
