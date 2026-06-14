from __future__ import annotations

from app.modules.github.prompt_builder import build_github_user_prompt
from prompts.github.parse import GITHUB_SYSTEM_PROMPT, GITHUB_USER_PROMPT_RULES


def test_github_system_prompt_encourages_inference_from_readme() -> None:
    assert "infer" in GITHUB_SYSTEM_PROMPT.lower()


def test_github_user_prompt_rules_do_not_use_section_aliases() -> None:
    assert "section_aliases" not in GITHUB_USER_PROMPT_RULES.lower()
    assert "{repo_name}" in GITHUB_USER_PROMPT_RULES


def test_build_github_user_prompt_includes_readme_text_and_format_instructions() -> None:
    prompt = build_github_user_prompt(
        repo_name="my-app",
        readme_text="# My App\nBuilt with FastAPI and React.",
        format_instructions='{"summary": "string"}',
    )

    assert "my-app" in prompt
    assert "FastAPI" in prompt
    assert "summary" in prompt
    assert "Infer tech_stack.backend" in prompt
