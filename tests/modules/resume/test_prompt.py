from __future__ import annotations

from app.modules.resume.prompt import (
    RESUME_SYSTEM_PROMPT,
    RESUME_USER_PROMPT_RULES,
    build_resume_user_prompt,
)


def test_resume_system_prompt_is_non_empty() -> None:
    assert "resume parsing agent" in RESUME_SYSTEM_PROMPT


def test_resume_user_prompt_rules_include_section_aliases_placeholder() -> None:
    assert "{section_aliases_json}" in RESUME_USER_PROMPT_RULES


def test_build_resume_user_prompt_includes_resume_text_and_format_instructions() -> None:
    prompt = build_resume_user_prompt(
        resume_text="Aryan Pahari",
        section_aliases_json='{"skills": ["skills"]}',
        format_instructions='{"candidate_name": "string"}',
    )

    assert "Aryan Pahari" in prompt
    assert '"skills"' in prompt
    assert "candidate_name" in prompt
