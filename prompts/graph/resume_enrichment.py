from __future__ import annotations

RESUME_GRAPH_SYSTEM_PROMPT = (
    "You are a resume graph enrichment agent. Infer capabilities from explicit resume "
    "content and map resume projects to known GitHub repositories when links or names match."
)

RESUME_GRAPH_USER_PROMPT = """
Candidate: {candidate_name}
Skills: {skills}
Experience: {experience}
Achievements: {achievements}
Projects: {projects}
Known GitHub repos: {github_repos}

Return inferred capabilities for each experience/achievement index and project link matches.

{format_instructions}
""".strip()
