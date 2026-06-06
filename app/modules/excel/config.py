from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from app.modules.excel.validator import validate_excel_parser_config

DEFAULT_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
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


@dataclass(frozen=True)
class ExcelParserConfig:
    """Controls how uploaded or remote Excel files are read."""

    sheet_count: int | None = 1
    max_rows: int | None = None
    max_empty_ratio: float | None = 0.9
    header_row: int = 1
    sheet_names: tuple[str, ...] = ()
    column_aliases: Mapping[str, tuple[str, ...]] = field(
        default_factory=lambda: DEFAULT_COLUMN_ALIASES
    )
    download_timeout_seconds: int = 20
    max_download_bytes: int = 10 * 1024 * 1024

    def validate(self) -> None:
        validate_excel_parser_config(self)
