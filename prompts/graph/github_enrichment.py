from __future__ import annotations

GITHUB_GRAPH_SYSTEM_PROMPT = (
    "You are a project knowledge-graph enrichment agent. Infer structured capabilities, "
    "domains, and impact signals from README content. Use evidence from the README only."
)

GITHUB_GRAPH_USER_PROMPT = """
Repository: {repo_name}
Summary: {summary}
Tech stack: {tech_stack}
Non-tech tags: {non_tech_tags}

Extract graph enrichment fields:
- capabilities: demonstrated skills such as RAG, workflow automation, MLOps
- domains: industry or problem domains such as recruitment, agriculture
- problems_solved: concrete problems the project addresses
- complexity: low, medium, or high
- business_impact: short phrase describing impact
- impact_signals: deployment or production signals such as deployed, multi-tenant

{format_instructions}

README excerpt:
{readme_text}
""".strip()
