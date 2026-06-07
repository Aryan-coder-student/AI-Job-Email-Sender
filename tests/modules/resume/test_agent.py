from __future__ import annotations

import json

from app.modules.llm.interface import LLMRequest, LLMResponse
from app.modules.resume.agent import extract_resume_structure_with_llm
from app.modules.resume.config import ResumeParserConfig


class FakeResumeRouter:
    def __init__(self) -> None:
        self.requests: list[LLMRequest] = []

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return LLMResponse(
            content=json.dumps(
                {
                    "candidate_name": "Aryan Pahari",
                    "summary": "Backend engineer.",
                    "skills": ["Python"],
                    "experience": [{"company_name": "Acme", "date": "1/2022 - 4/2022", "description": "Backend Engineer"}],
                    "projects": [{"project_name": "AI Job Email Agent", "link": None, "description": "built it"}],
                    "courses": [{"name": "AI Course", "description": "learned AI"}],
                    "certifications": [{"name": "AWS Certified", "link": "link"}],
                    "achievements": ["Won hackathon"],
                    "research": ["RAG evaluation"],
                    "education": ["B.Tech"],
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


def test_extract_resume_structure_with_llm() -> None:
    router = FakeResumeRouter()

    parsed_resume = extract_resume_structure_with_llm(
        cleaned_text="Aryan Pahari\nPython backend engineer",
        filename="resume.txt",
        file_extension=".txt",
        llm_router=router,  # type: ignore[arg-type]
        config=ResumeParserConfig(),
    )

    request = router.requests[0]
    assert "Extract structured resume data based on the provided text." in request.messages[1].content
    assert parsed_resume.candidate_name == "Aryan Pahari"
    assert parsed_resume.metadata["llm_provider"] == "fake"
