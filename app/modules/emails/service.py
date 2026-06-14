from __future__ import annotations

from app.core.exceptions import EmailDraftError
from app.core.logger import get_logger
from app.modules.emails.model import DraftGenerationRequest, EmailDraft
from app.modules.emails.prompt_builder import build_draft_user_prompt
from app.modules.emails.schemas import email_draft_parser
from app.modules.emails.utils import append_github_links_to_body, append_github_links_to_html
from app.modules.llm.interface import LLMMessage, LLMRequest
from app.modules.llm.router import LLMRouter
from prompts.emails.draft import DRAFT_SYSTEM_PROMPT

logger = get_logger(__name__)


def generate_application_draft(
    request: DraftGenerationRequest,
    *,
    llm_router: LLMRouter,
    max_tokens: int = 800,
) -> EmailDraft:
    recipient = request.recipient_email or request.company_record.get("hr_email")
    if not recipient or not str(recipient).strip():
        raise EmailDraftError("Recipient email is required to generate an application draft.")

    top_match = request.top_match or {}
    user_prompt = build_draft_user_prompt(
        candidate_name=request.candidate_name,
        candidate_summary=request.candidate_summary,
        candidate_skills=request.candidate_skills,
        company_name=request.company_name,
        company_description=request.company_record.get("company_description"),
        job_description=request.company_record.get("job_description"),
        role=request.company_record.get("role"),
        top_match=top_match,
        format_instructions=email_draft_parser.get_format_instructions(),
    )

    response = llm_router.generate(
        LLMRequest(
            messages=[
                LLMMessage(role="system", content=DRAFT_SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            temperature=0.3,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
    )

    try:
        parsed = email_draft_parser.parse(response.content)
    except Exception as error:
        raise EmailDraftError(f"Could not parse email draft response: {error}") from error

    body_text = append_github_links_to_body(
        parsed.body_text.strip(),
        github_projects=request.github_projects,
        top_match=top_match,
    )
    body_html = append_github_links_to_html(
        parsed.body_html.strip() if parsed.body_html else None,
        github_projects=request.github_projects,
        top_match=top_match,
    )

    draft_id = EmailDraft.new_id()
    logger.info(
        "Generated application draft draft_id=%s company=%s project=%s",
        draft_id,
        request.company_name,
        top_match.get("project_name"),
    )

    return EmailDraft(
        draft_id=draft_id,
        to=str(recipient).strip(),
        subject=parsed.subject.strip(),
        body_text=body_text,
        body_html=body_html,
        company_name=request.company_name,
        project_name=top_match.get("project_name"),
        status="draft",
        metadata={
            "llm_provider": response.provider,
            "top_match": top_match,
        },
    )
