from __future__ import annotations

from app.modules.llm.router import LLMRouter
from app.modules.resume.config import ResumeParserConfig
from app.modules.resume.model import ParsedResume
from app.modules.resume.utils import (
    build_parsed_resume_from_structure,
    build_resume_structure_request,
    parse_resume_structure_response,
)


def extract_resume_structure_with_llm(
    *,
    cleaned_text: str,
    filename: str | None,
    file_extension: str,
    llm_router: LLMRouter,
    config: ResumeParserConfig,
) -> ParsedResume:
    response = llm_router.generate(
        build_resume_structure_request(
            cleaned_text,
            config,
        )
    )
    structure = parse_resume_structure_response(response.content)

    return build_parsed_resume_from_structure(
        filename=filename,
        file_extension=file_extension,
        raw_text=cleaned_text,
        structure=structure,
        metadata={
            "raw_text_length": len(cleaned_text),
            "llm_provider": response.provider,
            "llm_model": response.model,
        },
    )
