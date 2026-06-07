from __future__ import annotations

import pytest

from app.core.exceptions import InvalidResumeError
from app.modules.resume.config import ResumeParserConfig
from app.modules.resume.utils import (
    build_parsed_resume_from_structure,
    build_resume_structure_request,

    build_text_only_resume,
    clean_resume_text,
    parse_resume_structure_response,
    split_resume_lines,
    truncate_resume_text,
)


def test_clean_resume_text_normalizes_spacing_and_newlines() -> None:
    assert clean_resume_text("Hello\x00   world\r\n\r\n\r\nNext") == "Hello world\n\nNext"


def test_split_resume_lines_returns_non_empty_trimmed_lines() -> None:
    assert split_resume_lines(" A \n\n B ") == ["A", "B"]


def test_truncate_resume_text_cleans_before_limiting() -> None:
    assert truncate_resume_text("  Python   backend engineer  ", max_chars=14) == "Python backend"


def test_truncate_resume_text_keeps_short_text_unchanged_after_cleaning() -> None:
    assert truncate_resume_text("  Python\n\nFastAPI  ", max_chars=100) == "Python\n\nFastAPI"





def test_build_resume_structure_request_asks_for_strict_json_fields() -> None:
    request = build_resume_structure_request(
        "Aryan Pahari\nPython backend engineer",
        ResumeParserConfig(llm_max_tokens=900),
    )

    assert request.temperature == 0
    assert request.max_tokens == 900
    assert request.response_format == {"type": "json_object"}
    prompt = request.messages[-1].content
    assert "candidate_name" in prompt
    assert "achievements" in prompt
    assert "research" in prompt
    assert "Aryan Pahari" in prompt





def test_parse_resume_structure_response_accepts_fenced_json() -> None:
    parsed = parse_resume_structure_response(
        """```json
{"candidate_name": "Aryan Pahari", "skills": ["Python"]}
```"""
    )

    assert parsed["candidate_name"] == "Aryan Pahari"
    assert parsed["skills"] == ["Python"]


def test_parse_resume_structure_response_rejects_invalid_json() -> None:
    with pytest.raises(InvalidResumeError, match="invalid resume JSON"):
        parse_resume_structure_response("just some random text")


def test_parse_resume_structure_response_rejects_non_object_json() -> None:
    with pytest.raises(InvalidResumeError):
        parse_resume_structure_response('["Python"]')


def test_build_parsed_resume_from_structure_normalizes_values() -> None:
    parsed_resume = build_parsed_resume_from_structure(
        filename="resume.txt",
        file_extension=".txt",
        raw_text="resume text",
        structure={
            "candidate_name": " Aryan Pahari ",
            "summary": " Backend engineer ",
            "skills": [" Python ", "", 123],
            "experience": ["Backend Engineer"],
            "projects": ["AI Job Email Agent"],
            "achievements": ["Won hackathon"],
            "research": ["RAG evaluation"],
            "education": ["B.Tech"],
            "links": {
                "emails": [" aryan@example.com "],
                "phones": [],
                "github": " https://github.com/aryan ",
                "linkedin": "",
                "portfolio": None,
                "urls": [" https://github.com/aryan "],
            },
        },
        metadata={"llm_provider": "fake"},
    )

    assert parsed_resume.candidate_name == "Aryan Pahari"
    assert parsed_resume.summary == "Backend engineer"
    assert parsed_resume.skills == ["Python"]
    assert parsed_resume.achievements == ["Won hackathon"]
    assert parsed_resume.research == ["RAG evaluation"]
    assert parsed_resume.links.emails == ["aryan@example.com"]
    assert parsed_resume.links.github == "https://github.com/aryan"
    assert parsed_resume.links.linkedin is None
    assert parsed_resume.metadata == {"llm_provider": "fake"}


def test_build_text_only_resume_has_empty_structured_fields() -> None:
    parsed_resume = build_text_only_resume(
        filename="resume.txt",
        file_extension=".txt",
        raw_text="resume text",
    )

    assert parsed_resume.candidate_name is None
    assert parsed_resume.summary == ""
    assert parsed_resume.skills == []
    assert parsed_resume.achievements == []
    assert parsed_resume.research == []
    assert parsed_resume.metadata == {
        "raw_text_length": len("resume text"),
        "structured_by": None,
    }
