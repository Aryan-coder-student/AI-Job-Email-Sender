from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

from docx import Document
from pypdf import PdfReader

from app.core.exceptions import InvalidResumeError
from app.core.logger import get_logger
from app.modules.resume.agent import extract_resume_structure_with_llm
from app.modules.resume.config import ResumeParserConfig
from app.modules.resume.model import ParsedResume
from app.modules.resume.utils import build_text_only_resume, truncate_resume_text
from app.modules.resume.validator import (
    validate_resume_content,
    validate_resume_filename,
    validate_resume_text,
)

if TYPE_CHECKING:
    from app.modules.llm.router import LLMRouter

logger = get_logger(__name__)


def parse_resume_from_upload(
    file_content: bytes,
    filename: str | None,
    config: ResumeParserConfig | None = None,
    llm_router: LLMRouter | None = None,
) -> ParsedResume:
    active_config = config or ResumeParserConfig()
    active_config.validate()
    extension = validate_resume_filename(filename, active_config.allowed_extensions)
    validate_resume_content(file_content, active_config.max_file_size_bytes)

    raw_text = _extract_text(file_content, extension)
    cleaned_text = truncate_resume_text(raw_text, active_config.max_cleaned_text_chars)
    validate_resume_text(cleaned_text)
    logger.info(
        "Parsing resume filename=%s extension=%s llm=%s text_chars=%s",
        filename,
        extension,
        llm_router is not None,
        len(cleaned_text),
    )

    if llm_router is None:
        logger.debug("Returning text-only resume for filename=%s", filename)
        return build_text_only_resume(
            filename=filename,
            file_extension=extension,
            raw_text=cleaned_text,
        )

    return extract_resume_structure_with_llm(
        cleaned_text=cleaned_text,
        filename=filename,
        file_extension=extension,
        llm_router=llm_router,
        config=active_config,
    )


def parse_resume_from_path(
    path: str | Path,
    config: ResumeParserConfig | None = None,
    llm_router: LLMRouter | None = None,
) -> ParsedResume:
    file_path = Path(path)

    try:
        file_content = file_path.read_bytes()
    except OSError as error:
        logger.exception("Could not read resume file path=%s", file_path)
        raise InvalidResumeError(f"Could not read resume file: {error}") from error

    return parse_resume_from_upload(
        file_content=file_content,
        filename=file_path.name,
        config=config,
        llm_router=llm_router,
    )


def _extract_text(file_content: bytes, extension: str) -> str:
    if extension == ".txt":
        return _parse_txt_content(file_content)

    if extension == ".pdf":
        return _parse_pdf_content(file_content)

    if extension == ".docx":
        return _parse_docx_content(file_content)

    raise InvalidResumeError(f"Unsupported resume extension: {extension}")


def _parse_txt_content(file_content: bytes) -> str:
    if file_content.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return file_content.decode("utf-16")
        except UnicodeDecodeError:
            pass

    for encoding in ("utf-8", "latin-1"):
        try:
            return file_content.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise InvalidResumeError("Could not decode text resume.")


def _parse_pdf_content(file_content: bytes) -> str:
    if PdfReader is None:
        raise InvalidResumeError(
            "pypdf is required to parse PDF resumes. Install dependencies from requirements.txt."
        )

    try:
        reader = PdfReader(BytesIO(file_content))
        text_parts = []
        links = []
        
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
            
            if "/Annots" in page:
                for annot_ref in page["/Annots"]:
                    annot = annot_ref.get_object()
                    if annot.get("/Subtype") == "/Link" and "/A" in annot:
                        action = annot["/A"].get_object()
                        if "/URI" in action:
                            links.append(action["/URI"])
                            
        full_text = "\n".join(text_parts)
        if links:
            full_text += "\n\nExtracted Embedded Hyperlinks:\n" + "\n".join(links)
            
        return full_text
    except Exception as error:
        logger.exception("Could not parse PDF resume")
        raise InvalidResumeError(f"Could not parse PDF resume: {error}") from error


def _parse_docx_content(file_content: bytes) -> str:
    if Document is None:
        raise InvalidResumeError(
            "python-docx is required to parse DOCX resumes. Install dependencies from requirements.txt."
        )

    try:
        document = Document(BytesIO(file_content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    except Exception as error:
        logger.exception("Could not parse DOCX resume")
        raise InvalidResumeError(f"Could not parse DOCX resume: {error}") from error
