from __future__ import annotations

import os
from typing import Any


EXCEL_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "company_name": (
        "company",
        "company name",
        "company_name",
        "name",
        "organization",
        "organisation",
        "employer",
    ),
    "company_url": (
        "company url",
        "company_url",
        "company website",
        "company website url",
        "official website",
        "official website url",
        "website",
        "website url",
        "website_url",
        "link to website",
        "link_to_website",
        "site",
    ),
    "company_linkedin_url": (
        "company linkedin",
        "company linkedin url",
        "company_linkedin",
        "company_linkedin_url",
        "linkedin company",
        "linkedin company url",
        "linkedin page",
        "linkedin page url",
        "linkedin",
    ),
    "job_url": (
        "job url",
        "job_url",
        "job link",
        "job_link",
        "job posting",
        "job posting url",
        "job post",
        "job post url",
        "opening url",
        "opening link",
        "application url",
        "application link",
        "apply url",
        "apply link",
        "careers page",
        "careers link",
        "career page",
        "career link",
        "jobpage",
        "job page",
        "jobpage url",
        "job page url",
        "link to jobpage",
        "link_to_jobpage",
        "link to job page",
        "link_to_job_page",
    ),
    "company_description": (
        "description",
        "company description",
        "company_description",
        "about",
        "about company",
        "summary",
        "what do they do",
        "what do they do verbatim",
        "what do they do (verbatim 10 words max.)",
        "what do they do (verbatim - 10 words max.)",
    ),
    "hr_email": (
        "hr email",
        "hr_email",
        "recruiter email",
        "contact email",
        "email",
        "mail",
    ),
    "contact_name": (
        "hr name",
        "recruiter name",
        "contact name",
        "person name",
    ),
    "role": (
        "role",
        "position",
        "job title",
        "job_title",
    ),
}


RESUME_ALLOWED_EXTENSIONS = (".txt", ".pdf", ".docx")

RESUME_SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "work history",
    ),
    "projects": (
        "projects",
        "project experience",
        "selected projects",
    ),
    "achievements": (
        "achievements",
        "accomplishments",
        "awards",
        "honors",
        "highlights",
    ),
    "research": (
        "research",
        "research work",
        "publications",
        "papers",
        "patents",
    ),
    "education": (
        "education",
        "academic background",
        "academics",
    ),
    "skills": (
        "skills",
        "technical skills",
        "technologies",
        "tools",
    ),
}

RESUME_STRUCTURE_FIELDS = (
    "candidate_name",
    "summary",
    "skills",
    "experience",
    "projects",
    "achievements",
    "research",
    "education",
    "links",
)


GROQ_KEY_ENV_VARS = (
    "GROQ_API_KEY_1",
    "GROQ_API_KEY_2",
    "GROQ_API_KEY_3",
    "GROQ_API_KEY_4",
)


def get_env(name: str, default: Any = None) -> Any:
    return os.getenv(name, default)
