from __future__ import annotations

import pytest

from app.core.exceptions import InvalidGitHubError
from app.modules.github.config import GitHubParserConfig
from app.modules.github.utils import (
    build_github_project_structure_request,
    build_parsed_github_project_from_structure,
    build_parsed_github_profile,
    clean_readme_text,
    extract_github_username,
    parse_github_project_structure_response,
    truncate_readme_text,
)
from app.modules.github.validator import validate_github_parser_config, validate_github_url


def test_clean_readme_text_normalizes_spacing_and_newlines() -> None:
    assert clean_readme_text("Hello\x00   world\r\n\r\n\r\nNext") == "Hello world\n\nNext"


def test_truncate_readme_text_cleans_before_limiting() -> None:
    assert truncate_readme_text("  FastAPI   backend  ", max_chars=14) == "FastAPI backen"


def test_extract_github_username_from_profile_url() -> None:
    assert extract_github_username("https://github.com/Aryan-coder-student") == "Aryan-coder-student"


def test_extract_github_username_from_repo_url() -> None:
    assert (
        extract_github_username("https://github.com/Aryan-coder-student/my-app")
        == "Aryan-coder-student"
    )


def test_extract_github_username_accepts_bare_domain() -> None:
    assert extract_github_username("github.com/aryan") == "aryan"


def test_extract_github_username_rejects_invalid_url() -> None:
    with pytest.raises(InvalidGitHubError, match="github.com"):
        extract_github_username("https://gitlab.com/aryan")


def test_validate_github_url_rejects_empty_value() -> None:
    with pytest.raises(InvalidGitHubError, match="required"):
        validate_github_url("  ")


def test_build_github_project_structure_request_asks_for_strict_json_fields() -> None:
    request = build_github_project_structure_request(
        repo_name="my-app",
        cleaned_readme="# My App\nBuilt with FastAPI and React.",
        config=GitHubParserConfig(llm_max_tokens=900),
    )

    assert request.temperature == 0
    assert request.max_tokens == 900
    assert request.response_format == {"type": "json_object"}
    prompt = request.messages[-1].content
    assert "Infer tech_stack.backend" in prompt
    assert "tech_stack" in prompt
    assert "deployed_link" in prompt
    assert "my-app" in prompt


def test_parse_github_project_structure_response_accepts_null_list_fields() -> None:
    parsed = parse_github_project_structure_response(
        """{
  "summary": "Immunization prediction model.",
  "tech_stack": {
    "backend": ["CatBoostClassifier"],
    "frontend": null,
    "ai_ml": ["Machine Learning"]
  },
  "non_tech_tags": null,
  "deployed_link": null
}"""
    )

    assert parsed["tech_stack"]["frontend"] == []
    assert parsed["non_tech_tags"] == []


def test_parse_github_project_structure_response_accepts_fenced_json() -> None:
    parsed = parse_github_project_structure_response(
        """```json
{
  "summary": "Task manager app.",
  "tech_stack": {"backend": ["Python"], "frontend": ["React"], "ai_ml": []},
  "non_tech_tags": ["productivity"],
  "deployed_link": "https://my-app.vercel.app"
}
```"""
    )

    assert parsed["summary"] == "Task manager app."
    assert parsed["tech_stack"]["backend"] == ["Python"]


def test_parse_github_project_structure_response_rejects_invalid_json() -> None:
    with pytest.raises(InvalidGitHubError, match="invalid GitHub project JSON"):
        parse_github_project_structure_response("not json")


def test_build_parsed_github_project_from_structure_normalizes_values() -> None:
    project = build_parsed_github_project_from_structure(
        repo_name="my-app",
        repo_link="https://github.com/aryan/my-app",
        raw_readme="README",
        structure={
            "summary": "  Task manager app.  ",
            "tech_stack": {
                "backend": [" Python "],
                "frontend": [" React "],
                "ai_ml": [" LangChain "],
            },
            "non_tech_tags": [" productivity "],
            "deployed_link": " https://my-app.vercel.app ",
        },
    )

    assert project.summary == "Task manager app."
    assert project.tech_stack.backend == ["Python"]
    assert project.tech_stack.frontend == ["React"]
    assert project.tech_stack.ai_ml == ["LangChain"]
    assert project.non_tech_tags == ["productivity"]
    assert project.deployed_link == "https://my-app.vercel.app"


def test_build_parsed_github_profile_serializes_projects() -> None:
    project = build_parsed_github_project_from_structure(
        repo_name="my-app",
        repo_link="https://github.com/aryan/my-app",
        raw_readme="README",
        structure={"summary": "Demo", "tech_stack": {}, "non_tech_tags": []},
    )
    profile = build_parsed_github_profile(
        github_username="aryan",
        github_url="https://github.com/aryan",
        projects=[project],
        metadata={"repos_parsed": 1},
    )

    payload = profile.to_dict()
    assert payload["github_username"] == "aryan"
    assert payload["projects"][0]["repo_name"] == "my-app"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_repos": 0}, "max_repos must be at least 1"),
        ({"min_readme_chars": 0}, "min_readme_chars must be at least 1"),
        ({"max_readme_chars": 0}, "max_readme_chars must be at least 1"),
        ({"llm_max_tokens": 0}, "llm_max_tokens must be at least 1"),
        ({"llm_max_workers": 0}, "llm_max_workers must be at least 1"),
    ],
)
def test_validate_github_parser_config_rejects_invalid_values(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_github_parser_config(GitHubParserConfig(**kwargs))
