from __future__ import annotations

import json

import pytest

import app.modules.resume.parser as parser_module
from app.core.exceptions import InvalidResumeError
from app.modules.llm.interface import LLMRequest, LLMResponse
from app.modules.resume.config import ResumeParserConfig
from app.modules.resume.parser import (
    _parse_docx_content,
    _parse_pdf_content,
    _parse_txt_content,
    parse_resume_from_path,
    parse_resume_from_upload,
)


RESUME_TEXT = """Aryan Pahari
aryan@example.com
https://github.com/aryan

Skills
Python, FastAPI

Experience
Backend Engineer

Projects
AI Job Email Agent

Achievements
Won a national hackathon

Research
Worked on RAG evaluation for job matching

Education
B.Tech Computer Science
"""


class FakeResumeRouter:
    def __init__(self) -> None:
        self.requests: list[LLMRequest] = []

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return LLMResponse(
            content=json.dumps(
                {
                    "candidate_name": "Aryan Pahari",
                    "summary": "Backend engineer building AI job automation tools.",
                    "skills": ["Python", "FastAPI"],
                    "experience": ["Backend Engineer"],
                    "projects": ["AI Job Email Agent"],
                    "achievements": ["Won a national hackathon"],
                    "research": ["Worked on RAG evaluation for job matching"],
                    "education": ["B.Tech Computer Science"],
                    "links": {
                        "emails": ["aryan@example.com"],
                        "phones": [],
                        "github": "https://github.com/aryan",
                        "linkedin": None,
                        "portfolio": None,
                        "urls": ["https://github.com/aryan"],
                    },
                }
            ),
            provider="fake",
            model="fake-model",
        )


def test_parse_resume_from_upload_returns_text_only_without_llm_router() -> None:
    parsed_resume = parse_resume_from_upload(
        RESUME_TEXT.encode("utf-8"),
        filename="resume.txt",
    )

    assert parsed_resume.filename == "resume.txt"
    assert parsed_resume.file_extension == ".txt"
    assert parsed_resume.raw_text == RESUME_TEXT.strip()
    assert parsed_resume.candidate_name is None
    assert parsed_resume.skills == []
    assert parsed_resume.experience == []
    assert parsed_resume.projects == []
    assert parsed_resume.achievements == []
    assert parsed_resume.research == []
    assert parsed_resume.education == []
    assert parsed_resume.links.emails == []
    assert parsed_resume.to_dict()["metadata"]["structured_by"] is None


def test_parse_resume_from_upload_uses_llm_router_for_structured_output() -> None:
    router = FakeResumeRouter()

    parsed_resume = parse_resume_from_upload(
        RESUME_TEXT.encode("utf-8"),
        filename="resume.txt",
        llm_router=router,  # type: ignore[arg-type]
    )

    assert parsed_resume.candidate_name == "Aryan Pahari"
    assert parsed_resume.summary == "Backend engineer building AI job automation tools."
    assert parsed_resume.skills == ["Python", "FastAPI"]
    assert parsed_resume.experience == ["Backend Engineer"]
    assert parsed_resume.projects == ["AI Job Email Agent"]
    assert parsed_resume.achievements == ["Won a national hackathon"]
    assert parsed_resume.research == ["Worked on RAG evaluation for job matching"]
    assert parsed_resume.education == ["B.Tech Computer Science"]
    assert parsed_resume.links.emails == ["aryan@example.com"]
    assert parsed_resume.links.github == "https://github.com/aryan"
    assert parsed_resume.metadata["llm_provider"] == "fake"
    assert parsed_resume.metadata["llm_model"] == "fake-model"
    assert router.requests[0].response_format == {"type": "json_object"}


def test_parse_resume_from_upload_truncates_cleaned_text_before_llm() -> None:
    router = FakeResumeRouter()

    parsed_resume = parse_resume_from_upload(
        b"  abc   def  ",
        filename="resume.txt",
        config=ResumeParserConfig(max_cleaned_text_chars=5),
        llm_router=router,  # type: ignore[arg-type]
    )

    assert parsed_resume.raw_text == "abc d"
    assert "abc d" in router.requests[0].messages[-1].content
    assert "abc def" not in router.requests[0].messages[-1].content


def test_parse_resume_from_path_reads_local_file(tmp_path) -> None:
    resume_path = tmp_path / "resume.txt"
    resume_path.write_text(RESUME_TEXT, encoding="utf-8")

    parsed_resume = parse_resume_from_path(resume_path)

    assert parsed_resume.filename == "resume.txt"
    assert parsed_resume.raw_text == RESUME_TEXT.strip()


def test_parse_resume_from_path_wraps_read_error(tmp_path) -> None:
    with pytest.raises(InvalidResumeError, match="Could not read resume file"):
        parse_resume_from_path(tmp_path / "missing.txt")


def test_parse_resume_from_upload_rejects_unsupported_file() -> None:
    with pytest.raises(InvalidResumeError, match="Unsupported resume file type"):
        parse_resume_from_upload(b"resume", filename="resume.csv")


def test_parse_resume_from_upload_rejects_empty_extracted_text() -> None:
    with pytest.raises(InvalidResumeError, match="did not extract any text"):
        parse_resume_from_upload(b"   ", filename="resume.txt")


def test_parse_txt_content_falls_back_to_latin_1() -> None:
    assert _parse_txt_content("café".encode("latin-1")) == "café"


def test_parse_pdf_content_reports_missing_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(parser_module, "PdfReader", None)

    with pytest.raises(InvalidResumeError, match="pypdf is required"):
        _parse_pdf_content(b"not pdf")


def test_parse_docx_content_reports_missing_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(parser_module, "Document", None)

    with pytest.raises(InvalidResumeError, match="python-docx is required"):
        _parse_docx_content(b"not docx")
