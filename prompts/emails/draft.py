from __future__ import annotations

DRAFT_SYSTEM_PROMPT = (
    "You write concise, specific job application emails. "
    "Reference the candidate's strongest matching project and why it fits the company. "
    "Keep the tone professional and direct."
)

DRAFT_USER_PROMPT = """
Write a concise job application email.

Candidate: {candidate_name}
Summary: {candidate_summary}
Skills: {candidate_skills_json}

Company: {company_name}
Company description: {company_description}
Job description: {job_description}
Role: {role}

Top matching project: {project_name}
Why this project fits: {explanation}
Graph score: {graph_score}
Embedding score: {embedding_score}
LLM score: {llm_score}
Graph paths: {graph_paths_json}

{format_instructions}
""".strip()
