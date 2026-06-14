from __future__ import annotations

from prompts.resume.parse import RESUME_USER_PROMPT, RESUME_USER_PROMPT_RULES


def build_resume_user_prompt(
    *,
    resume_text: str,
    section_aliases_json: str,
    format_instructions: str,
) -> str:
    rules = RESUME_USER_PROMPT_RULES.format(section_aliases_json=section_aliases_json)
    return RESUME_USER_PROMPT.format(
        rules=rules,
        format_instructions=format_instructions,
        resume_text=resume_text,
    )
