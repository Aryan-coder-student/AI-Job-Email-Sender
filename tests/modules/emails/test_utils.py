from __future__ import annotations

from app.modules.emails.utils import (
    append_github_links_to_body,
    append_github_links_to_html,
    find_github_project,
    resolve_public_link,
)


def test_resolve_public_link_prefers_deployed_link() -> None:
    project = {
        "repo_link": "https://github.com/user/demo",
        "deployed_link": "https://demo.vercel.app",
    }

    assert resolve_public_link(project) == "https://demo.vercel.app"


def test_resolve_public_link_falls_back_to_repo_link() -> None:
    project = {
        "repo_link": "https://github.com/user/demo",
        "deployed_link": None,
    }

    assert resolve_public_link(project) == "https://github.com/user/demo"


def test_find_github_project_matches_normalized_name() -> None:
    projects = [
        {"repo_name": "AgroScan_Pro", "repo_link": "https://github.com/user/AgroScan_Pro"},
    ]

    match = find_github_project("agroscan-pro", projects)

    assert match is not None
    assert match["repo_name"] == "AgroScan_Pro"


def test_append_github_links_to_body_includes_deployed_and_repo_links() -> None:
    github_projects = [
        {
            "repo_name": "AgroScan_Pro",
            "repo_link": "https://github.com/user/AgroScan_Pro",
            "deployed_link": "https://agroscan.example.com",
        },
        {
            "repo_name": "AI-Club-Task-Round",
            "repo_link": "https://github.com/user/AI-Club-Task-Round",
            "deployed_link": None,
        },
    ]

    body = append_github_links_to_body(
        "Hello team,",
        github_projects=github_projects,
        top_match={"project_name": "AgroScan_Pro"},
    )

    assert "Hello team," in body
    assert "- AgroScan_Pro: https://agroscan.example.com" in body
    assert "- AI-Club-Task-Round: https://github.com/user/AI-Club-Task-Round" in body
    assert body.index("AgroScan_Pro") < body.index("AI-Club-Task-Round")


def test_append_github_links_to_html_builds_list() -> None:
    body_html = append_github_links_to_html(
        "<p>Hello team,</p>",
        github_projects=[
            {
                "repo_name": "demo",
                "repo_link": "https://github.com/user/demo",
                "deployed_link": "https://demo.example.com",
            }
        ],
        top_match={"project_name": "demo"},
    )

    assert body_html is not None
    assert 'href="https://demo.example.com"' in body_html
    assert ">demo</a>" in body_html
