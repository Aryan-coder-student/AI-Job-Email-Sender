from __future__ import annotations

import json
from unittest.mock import patch

from app.modules.github.agent import extract_project_structure_with_llm
from app.modules.github.config import GitHubParserConfig
from app.modules.github.model import GitHubRepoReadme
from app.modules.llm.interface import LLMRequest, LLMResponse


class FakeGitHubRouter:
    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content=json.dumps(
                {
                    "summary": "Demo project.",
                    "tech_stack": {"backend": ["Python"], "frontend": [], "ai_ml": []},
                    "non_tech_tags": [],
                    "deployed_link": None,
                }
            ),
            provider="fake",
            model="fake-model",
        )


def test_extract_project_structure_with_llm_returns_metadata() -> None:
    router = FakeGitHubRouter()
    repo = GitHubRepoReadme(
        repo_name="demo",
        repo_link="https://github.com/aryan/demo",
        raw_readme="# Demo\n" + ("x" * 100),
    )

    project, metadata = extract_project_structure_with_llm(
        repo=repo,
        llm_router=router,  # type: ignore[arg-type]
        config=GitHubParserConfig(),
    )

    assert project.repo_name == "demo"
    assert metadata["repo_name"] == "demo"
    assert metadata["llm_model"] == "fake-model"
