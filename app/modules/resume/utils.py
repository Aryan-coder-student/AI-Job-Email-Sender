from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

from app.core.exceptions import InvalidResumeError
from app.modules.llm.interface import LLMMessage, LLMRequest
from app.modules.resume.config import ResumeParserConfig
from app.modules.resume.schema import ParsedResume, ResumeLinks
from setting import RESUME_SECTION_ALIASES


class ResumeLinksSchema(BaseModel):
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    github: str | None = None
    linkedin: str | None = None
    portfolio: str | None = None
    urls: list[str] = Field(default_factory=list)


class ResumeStructureSchema(BaseModel):
    candidate_name: str | None = Field(
        default=None, description="Candidate name exactly as shown in the resume."
    )
    summary: str = Field(
        default="", description="Concise factual summary, max 3 sentences."
    )
    skills: list[str] = Field(
        default_factory=list, description="List of individual skills."
    )
    experience: list[str] = Field(
        default_factory=list, 
        description="List of work experiences. Each string MUST include the job title, company, dates, AND the full bullet point descriptions of responsibilities."
    )
    projects: list[str] = Field(
        default_factory=list, 
        description="List of projects. Each string MUST include the project name and the full description."
    )
    achievements: list[str] = Field(
        default_factory=list, 
        description="List of achievements, awards, and recognitions including full details."
    )
    research: list[str] = Field(
        default_factory=list, 
        description="List of research work, papers, or publications with descriptions."
    )
    education: list[str] = Field(
        default_factory=list, 
        description="List of educational qualifications including degree, institution, and dates."
    )
    links: ResumeLinksSchema = Field(default_factory=ResumeLinksSchema)


resume_parser = PydanticOutputParser(pydantic_object=ResumeStructureSchema)


def clean_resume_text(raw_text: str) -> str:
    text = raw_text.replace("\x00", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_resume_lines(raw_text: str) -> list[str]:
    return [line.strip() for line in raw_text.splitlines() if line.strip()]


def truncate_resume_text(raw_text: str, max_chars: int) -> str:
    cleaned_text = clean_resume_text(raw_text)

    if len(cleaned_text) <= max_chars:
        return cleaned_text

    return cleaned_text[:max_chars].rstrip()


def build_resume_structure_request(
    cleaned_text: str,
    config: ResumeParserConfig,
) -> LLMRequest:
    resume_text = cleaned_text[: config.max_cleaned_text_chars]
    section_aliases_json = json.dumps(RESUME_SECTION_ALIASES, indent=2)

    system_prompt = (
        "You are a resume parsing agent. Extract only facts explicitly present "
        "in the resume. Do not infer, embellish, or invent missing data."
    )
    user_prompt = f"""
Extract structured resume data based on the provided text.

Rules:
- Achievements include awards, measurable wins, honors, recognitions, competitions.
- Research includes papers, publications, patents, thesis, ML/AI research work.
- Preserve URLs exactly when possible.
- Section aliases that may appear:
{section_aliases_json}

{resume_parser.get_format_instructions()}

Resume text:
{resume_text}
""".strip()

    return LLMRequest(
        messages=[
            LLMMessage(role="system", content=system_prompt),
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

    return ParsedResume(
        filename=filename,
        file_extension=file_extension,
        raw_text=raw_text,
        candidate_name=_string_or_none(structure.get("candidate_name")),
        summary=_string_or_empty(structure.get("summary")),
        skills=_string_list(structure.get("skills")),
        experience=_string_list(structure.get("experience")),
        projects=_string_list(structure.get("projects")),
        achievements=_string_list(structure.get("achievements")),
        research=_string_list(structure.get("research")),
        education=_string_list(structure.get("education")),
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
        achievements=[],
        research=[],
        education=[],
        links=ResumeLinks(),
        metadata={
            "raw_text_length": len(raw_text),
            "structured_by": None,
        },
    )


def _extract_json_object(content: str) -> str:
    stripped_content = content.strip()
    fenced_match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        stripped_content,
        flags=re.DOTALL,
    )

    if fenced_match:
        return fenced_match.group(1)

    return stripped_content


def _normalise_links(value: Any) -> ResumeLinks:
    if not isinstance(value, dict):
        return ResumeLinks()

    return ResumeLinks(
        emails=_string_list(value.get("emails")),
        phones=_string_list(value.get("phones")),
        github=_string_or_none(value.get("github")),
        linkedin=_string_or_none(value.get("linkedin")),
        portfolio=_string_or_none(value.get("portfolio")),
        urls=_string_list(value.get("urls")),
    )


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _string_or_none(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()

    return None


def _string_or_empty(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()

    return ""
