from __future__ import annotations

from prompts.github.parse import GITHUB_USER_PROMPT, GITHUB_USER_PROMPT_RULES


def build_github_user_prompt(
    *,
    repo_name: str,
    readme_text: str,
    format_instructions: str,
) -> str:
    rules = GITHUB_USER_PROMPT_RULES.format(repo_name=repo_name)
    return GITHUB_USER_PROMPT.format(
        rules=rules,
        format_instructions=format_instructions,
        readme_text=readme_text,
    )
