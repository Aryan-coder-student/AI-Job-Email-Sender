from __future__ import annotations

import json
import threading
import time
from unittest.mock import patch

from app.modules.github.agent import extract_project_structure_with_llm
from app.modules.github.config import GitHubParserConfig
from app.modules.github.model import ParsedGitHubProject, GitHubRepoReadme, GitHubTechStack
from app.modules.github.parser import (
    _extract_projects_with_llm,
    parse_github_from_resume,
    parse_github_profile,
)
from app.modules.llm.interface import LLMRequest, LLMResponse
from app.modules.resume.model import ParsedResume, ResumeLinks


class FakeGitHubRouter:
    def __init__(self) -> None:
        self.requests: list[LLMRequest] = []

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return LLMResponse(
            content=json.dumps(
                {
                    "summary": "A full-stack task manager.",
                    "tech_stack": {
                        "backend": ["Python", "FastAPI"],
                        "frontend": ["React"],
                        "ai_ml": ["LangChain"],
                    },
                    "non_tech_tags": ["productivity"],
                    "deployed_link": "https://my-app.vercel.app",
                }
            ),
            provider="fake",
            model="fake-model",
        )


def _sample_repo() -> GitHubRepoReadme:
    return GitHubRepoReadme(
        repo_name="my-app",
        repo_link="https://github.com/aryan/my-app",
        raw_readme="# My App\nBuilt with FastAPI and React.",
    )


def test_extract_project_structure_with_llm() -> None:
    router = FakeGitHubRouter()

    project, metadata = extract_project_structure_with_llm(
        repo=_sample_repo(),
        llm_router=router,  # type: ignore[arg-type]
        config=GitHubParserConfig(),
    )

    assert "Extract structured project data" in router.requests[0].messages[1].content
    assert project.summary == "A full-stack task manager."
    assert project.tech_stack.backend == ["Python", "FastAPI"]
    assert project.deployed_link == "https://my-app.vercel.app"
    assert metadata["llm_provider"] == "fake"


@patch("app.modules.github.parser.fetch_user_repos_with_readmes")
def test_parse_github_profile_readme_only(mock_fetch) -> None:
    mock_fetch.return_value = (
        [_sample_repo()],
        [{"name": "empty-repo", "reason": "empty_readme"}],
    )

    profile = parse_github_profile(
        "https://github.com/aryan",
        llm_router=None,
    )

    assert profile.github_username == "aryan"
    assert profile.projects[0].repo_link == "https://github.com/aryan/my-app"
    assert profile.projects[0].summary == ""
    assert profile.metadata["structured_by"] is None
    assert profile.metadata["repos_parsed"] == 1


@patch("app.modules.github.parser.fetch_user_repos_with_readmes")
def test_parse_github_from_resume_uses_resume_github_link(mock_fetch) -> None:
    mock_fetch.return_value = ([_sample_repo()], [])
    router = FakeGitHubRouter()

    parsed_resume = ParsedResume(
        filename="resume.txt",
        file_extension=".txt",
        raw_text="resume",
        candidate_name="Aryan",
        summary="",
        skills=[],
        experience=[],
        projects=[],
        courses=[],
        certifications=[],
        achievements=[],
        research=[],
        education=[],
        links=ResumeLinks(github="https://github.com/aryan"),
    )

    profile = parse_github_from_resume(
        parsed_resume,
        llm_router=router,  # type: ignore[arg-type]
    )

    assert profile.github_username == "aryan"
    assert profile.projects[0].tech_stack.ai_ml == ["LangChain"]
    assert profile.metadata["structured_by"] == "llm"


def test_extract_projects_with_llm_runs_requests_in_parallel() -> None:
    repos = [
        GitHubRepoReadme(
            repo_name=f"repo-{index}",
            repo_link=f"https://github.com/aryan/repo-{index}",
            raw_readme=f"# Repo {index}\n" + ("x" * 100),
        )
        for index in range(3)
    ]
    active_requests = 0
    max_active_requests = 0
    lock = threading.Lock()

    def fake_extract(**kwargs):
        nonlocal active_requests, max_active_requests
        with lock:
            active_requests += 1
            max_active_requests = max(max_active_requests, active_requests)

        time.sleep(0.05)

        with lock:
            active_requests -= 1

        repo = kwargs["repo"]
        project = ParsedGitHubProject(
            repo_name=repo.repo_name,
            repo_link=repo.repo_link,
            deployed_link=None,
            summary="Demo",
            tech_stack=GitHubTechStack(),
            non_tech_tags=[],
            raw_readme=repo.raw_readme,
        )
        return project, {"repo_name": repo.repo_name}

    with patch(
        "app.modules.github.parser.extract_project_structure_with_llm",
        side_effect=fake_extract,
    ):
        projects, llm_runs = _extract_projects_with_llm(
            repos,
            llm_router=object(),  # type: ignore[arg-type]
            config=GitHubParserConfig(llm_max_workers=3),
        )

    assert len(projects) == 3
    assert [project.repo_name for project in projects] == [repo.repo_name for repo in repos]
    assert len(llm_runs) == 3
    assert max_active_requests > 1
