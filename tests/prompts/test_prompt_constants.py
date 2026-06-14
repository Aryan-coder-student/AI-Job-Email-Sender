from __future__ import annotations

import pytest

from prompts import (
    DRAFT_SYSTEM_PROMPT,
    DRAFT_USER_PROMPT,
    EMPLOYER_GRAPH_SYSTEM_PROMPT,
    EMPLOYER_GRAPH_USER_PROMPT,
    GITHUB_GRAPH_SYSTEM_PROMPT,
    GITHUB_GRAPH_USER_PROMPT,
    GITHUB_SYSTEM_PROMPT,
    GITHUB_USER_PROMPT,
    GITHUB_USER_PROMPT_RULES,
    RESUME_GRAPH_SYSTEM_PROMPT,
    RESUME_GRAPH_USER_PROMPT,
    RESUME_SYSTEM_PROMPT,
    RESUME_USER_PROMPT,
    RESUME_USER_PROMPT_RULES,
)


@pytest.mark.parametrize(
    ("prompt", "expected_phrase"),
    [
        (DRAFT_SYSTEM_PROMPT, "job application emails"),
        (DRAFT_USER_PROMPT, "{format_instructions}"),
        (RESUME_SYSTEM_PROMPT, "resume parsing agent"),
        (RESUME_USER_PROMPT_RULES, "{section_aliases_json}"),
        (RESUME_USER_PROMPT, "{resume_text}"),
        (GITHUB_SYSTEM_PROMPT, "README project analyzer"),
        (GITHUB_USER_PROMPT_RULES, "{repo_name}"),
        (GITHUB_USER_PROMPT, "{readme_text}"),
        (RESUME_GRAPH_SYSTEM_PROMPT, "resume graph enrichment"),
        (RESUME_GRAPH_USER_PROMPT, "{github_repos}"),
        (EMPLOYER_GRAPH_SYSTEM_PROMPT, "employer intelligence"),
        (EMPLOYER_GRAPH_USER_PROMPT, "{input_mode}"),
        (GITHUB_GRAPH_SYSTEM_PROMPT, "knowledge-graph enrichment"),
        (GITHUB_GRAPH_USER_PROMPT, "{readme_text}"),
    ],
)
def test_prompt_constants_are_non_empty(prompt: str, expected_phrase: str) -> None:
    assert prompt.strip()
    assert expected_phrase in prompt
