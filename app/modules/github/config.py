from __future__ import annotations

from dataclasses import dataclass

from app.modules.github.validator import validate_github_parser_config
from setting import GITHUB_TOKEN_ENV, get_env


@dataclass(frozen=True)
class GitHubParserConfig:
    github_token: str | None = None
    max_repos: int = 100
    min_readme_chars: int = 80
    max_readme_chars: int = 20000
    llm_max_tokens: int = 1500
    llm_max_workers: int = 5

    def __post_init__(self) -> None:
        if self.github_token is None:
            token = get_env(GITHUB_TOKEN_ENV)
            if isinstance(token, str) and token.strip():
                object.__setattr__(self, "github_token", token.strip())

    def validate(self) -> None:
        validate_github_parser_config(self)
