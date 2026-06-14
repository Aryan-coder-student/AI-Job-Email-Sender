from __future__ import annotations

EMPLOYER_GRAPH_SYSTEM_PROMPT = (
    "You are an employer intelligence agent. Extract hiring signals from company and/or "
    "job descriptions. Do not invent requirements that are not supported by the text."
)

EMPLOYER_GRAPH_USER_PROMPT = """
Company name: {company_name}
Role: {role}
Company description: {company_description}
Job description: {job_description}
Input mode: {input_mode}

Rules:
- If only company description is present, populate company_* fields.
- If only job description is present, populate job_required_* fields and infer domains from the JD.
- If both are present, keep company-level domains separate from job-level requirements.
- Set enrichment_source to company, job, or both.

{format_instructions}
""".strip()
