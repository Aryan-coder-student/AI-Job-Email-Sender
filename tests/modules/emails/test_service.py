from __future__ import annotations

import pytest

from app.modules.emails.model import DraftGenerationRequest, EmailDraft
from app.modules.emails.service import generate_application_draft
from app.modules.llm.interface import LLMRequest, LLMResponse


class FakeLLMRouter:
    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            provider="fake",
            model="fake",
            content='{"subject": "Application for 100Starlings", "body_text": "Hello team,"}',
        )


def test_generate_application_draft_parses_llm_response() -> None:
    request = DraftGenerationRequest(
        candidate_name="Aryan Pahari",
        candidate_summary="Backend developer",
        candidate_skills=["Python", "FastAPI"],
        company_name="100Starlings",
        company_record={
            "company_description": "Custom web/mobile dev",
            "hr_email": "hr@100starlings.com",
        },
        top_match={
            "project_name": "demo-project",
            "explanation": "Strong web fit",
            "paths": [],
        },
        github_projects=[
            {
                "repo_name": "demo-project",
                "repo_link": "https://github.com/user/demo-project",
                "deployed_link": "https://demo.example.com",
            }
        ],
    )

    draft = generate_application_draft(request, llm_router=FakeLLMRouter())

    assert draft.to == "hr@100starlings.com"
    assert draft.subject == "Application for 100Starlings"
    assert draft.body_text.startswith("Hello team,")
    assert "- demo-project: https://demo.example.com" in draft.body_text
    assert draft.company_name == "100Starlings"
    assert draft.project_name == "demo-project"
    assert draft.status == "draft"


def test_generate_application_draft_requires_recipient() -> None:
    request = DraftGenerationRequest(
        candidate_name="Aryan Pahari",
        candidate_summary=None,
        candidate_skills=[],
        company_name="100Starlings",
        company_record={"company_description": "Custom web/mobile dev"},
        top_match={},
    )

    with pytest.raises(Exception, match="Recipient email is required"):
        generate_application_draft(request, llm_router=FakeLLMRouter())
