from __future__ import annotations

from app.core.logger import get_logger
from app.modules.llm.router import LLMRouter
from app.modules.resume.config import ResumeParserConfig
from app.modules.resume.model import ParsedResume
from app.modules.resume.utils import (
    build_parsed_resume_from_structure,
    build_resume_structure_request,
    parse_resume_structure_response,
)


logger = get_logger(__name__)


def extract_resume_structure_with_llm(
    *,
    cleaned_text: str,
    filename: str | None,
    file_extension: str,
    llm_router: LLMRouter,
    config: ResumeParserConfig,
) -> ParsedResume:
    logger.debug("Extracting resume structure with LLM filename=%s", filename)
    response = llm_router.generate(
        build_resume_structure_request(
            cleaned_text,
            config,
        )
    )
    structure = parse_resume_structure_response(response.content)

    parsed_resume = build_parsed_resume_from_structure(
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
    logger.info(
        "Extracted resume structure filename=%s provider=%s model=%s",
        filename,
        response.provider,
        response.model,
    )
    return parsed_resume
