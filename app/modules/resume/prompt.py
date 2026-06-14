from __future__ import annotations

RESUME_SYSTEM_PROMPT = (
    "You are a resume parsing agent. Extract only facts explicitly present "
    "in the resume. Do not infer, embellish, or invent missing data."
)

RESUME_USER_PROMPT_RULES = """
Extract structured resume data based on the provided text.

Rules:
- Achievements include awards, measurable wins, honors, recognitions, competitions.
- Research includes papers, publications, patents, thesis, ML/AI research work.
- Preserve URLs exactly when possible.
- Section aliases that may appear:
{section_aliases_json}
""".strip()


def build_resume_user_prompt(
    *,
    resume_text: str,
    section_aliases_json: str,
    format_instructions: str,
) -> str:
    rules = RESUME_USER_PROMPT_RULES.format(section_aliases_json=section_aliases_json)

    return f"""
{rules}

{format_instructions}

Resume text:
{resume_text}
""".strip()
