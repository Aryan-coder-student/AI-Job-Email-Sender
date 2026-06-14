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

RESUME_USER_PROMPT = """
{rules}

{format_instructions}

Resume text:
{resume_text}
""".strip()
