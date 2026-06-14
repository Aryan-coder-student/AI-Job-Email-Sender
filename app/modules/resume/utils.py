from __future__ import annotations

import json
from typing import Any

from app.core.exceptions import InvalidResumeError
from app.core.logger import get_logger
from app.core.string_normalizers import string_list, string_or_empty, string_or_none
from app.core.text import clean_document_text, truncate_document_text
from app.modules.llm.interface import LLMMessage, LLMRequest
from app.modules.resume.config import ResumeParserConfig
from app.modules.resume.model import (
    ParsedResume,
    ResumeCertification,
    ResumeCourse,
    ResumeExperience,
    ResumeLinks,
    ResumeProject,
    resume_parser,
)
from app.modules.resume.prompt_builder import build_resume_user_prompt
from prompts.resume.parse import RESUME_SYSTEM_PROMPT

logger = get_logger(__name__)


def clean_resume_text(raw_text: str) -> str:
    return clean_document_text(raw_text)


def split_resume_lines(raw_text: str) -> list[str]:
    return [line.strip() for line in raw_text.splitlines() if line.strip()]


def truncate_resume_text(raw_text: str, max_chars: int) -> str:
    return truncate_document_text(raw_text, max_chars)


def build_resume_structure_request(
    cleaned_text: str,
    config: ResumeParserConfig,
) -> LLMRequest:
    resume_text = cleaned_text[: config.max_cleaned_text_chars]
    section_aliases_json = json.dumps(config.section_aliases, indent=2)
    user_prompt = build_resume_user_prompt(
        resume_text=resume_text,
        section_aliases_json=section_aliases_json,
        format_instructions=resume_parser.get_format_instructions(),
    )

    return LLMRequest(
        messages=[
            LLMMessage(role="system", content=RESUME_SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ],
        temperature=0,
        max_tokens=config.llm_max_tokens,
        response_format={"type": "json_object"},
    )


def parse_resume_structure_response(content: str) -> dict[str, Any]:
    try:
        parsed_obj = resume_parser.parse(content)
        return parsed_obj.model_dump()
    except Exception as error:
        logger.warning("Invalid resume JSON from LLM: %s", error)
        raise InvalidResumeError(
            f"LLM returned invalid resume JSON: {error}"
        ) from error


def build_parsed_resume_from_structure(
    *,
    filename: str | None,
    file_extension: str,
    raw_text: str,
    structure: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> ParsedResume:
    links = _normalise_links(structure.get("links"))

    experiences = []
    for exp in structure.get("experience", []):
        experiences.append(ResumeExperience(
            company_name=string_or_none(exp.get("company_name")),
            date=string_or_none(exp.get("date")),
            description=string_or_none(exp.get("description")),
        ))

    projects = []
    for proj in structure.get("projects", []):
        projects.append(ResumeProject(
            project_name=string_or_none(proj.get("project_name")),
            link=string_or_none(proj.get("link")),
            description=string_or_none(proj.get("description")),
        ))

    courses = []
    for course in structure.get("courses", []):
        courses.append(ResumeCourse(
            name=string_or_none(course.get("name")),
            description=string_or_none(course.get("description")),
        ))

    certifications = []
    for cert in structure.get("certifications", []):
        certifications.append(ResumeCertification(
            name=string_or_none(cert.get("name")),
            link=string_or_none(cert.get("link")),
        ))

    return ParsedResume(
        filename=filename,
        file_extension=file_extension,
        raw_text=raw_text,
        candidate_name=string_or_none(structure.get("candidate_name")),
        summary=string_or_empty(structure.get("summary")),
        skills=string_list(structure.get("skills")),
        experience=experiences,
        projects=projects,
        courses=courses,
        certifications=certifications,
        achievements=string_list(structure.get("achievements")),
        research=string_list(structure.get("research")),
        education=string_list(structure.get("education")),
        links=links,
        metadata=metadata or {},
    )


def build_text_only_resume(
    *,
    filename: str | None,
    file_extension: str,
    raw_text: str,
) -> ParsedResume:
    return ParsedResume(
        filename=filename,
        file_extension=file_extension,
        raw_text=raw_text,
        candidate_name=None,
        summary="",
        skills=[],
        experience=[],
        projects=[],
        courses=[],
        certifications=[],
        achievements=[],
        research=[],
        education=[],
        links=ResumeLinks(),
        metadata={
            "raw_text_length": len(raw_text),
            "structured_by": None,
        },
    )


def _normalise_links(value: Any) -> ResumeLinks:
    if not isinstance(value, dict):
        return ResumeLinks()

    return ResumeLinks(
        emails=string_list(value.get("emails")),
        phones=string_list(value.get("phones")),
        github=string_or_none(value.get("github")),
        linkedin=string_or_none(value.get("linkedin")),
        portfolio=string_or_none(value.get("portfolio")),
        urls=string_list(value.get("urls")),
    )
