from __future__ import annotations

GITHUB_SYSTEM_PROMPT = (
    "You are a GitHub README project analyzer. Read the entire README and infer "
    "structured project metadata from its content. Derive tech stack, summary, tags, "
    "and deployment links from dependencies, install steps, badges, feature descriptions, "
    "architecture notes, and domain language anywhere in the text. Do not invent "
    "technologies or URLs with no support in the README."
)

GITHUB_USER_PROMPT_RULES = """
Extract structured project data from the README below.

Rules:
- Infer tech_stack.backend from server-side languages, APIs, databases, and backend frameworks mentioned anywhere in the README.
- Infer tech_stack.frontend from UI frameworks, CSS libraries, and client-side tools mentioned anywhere in the README.
- Infer tech_stack.ai_ml from ML, AI, data science, computer vision, NLP, or LLM tools mentioned anywhere in the README.
- Write summary as a concise project overview (max 3 sentences) inferred from the README purpose, features, and outcomes.
- Infer non_tech_tags from the project domain or theme (for example: healthcare, agriculture, sports analytics, hackathon, e-commerce).
- Set deployed_link from demo badges, live site links, deployment URLs, or hosted app mentions; use null only if no deployment link appears.
- Use empty lists or null only when the README gives no reasonable signal for that field.
- For list fields, return [] instead of null when empty.
- Preserve URLs exactly when found.

Repository name: {repo_name}
""".strip()


def build_github_user_prompt(
    *,
    repo_name: str,
    readme_text: str,
    format_instructions: str,
) -> str:
    rules = GITHUB_USER_PROMPT_RULES.format(repo_name=repo_name)

    return f"""
{rules}

{format_instructions}

README text:
{readme_text}
""".strip()
