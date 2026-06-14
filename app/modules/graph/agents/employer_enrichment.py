from __future__ import annotations

from app.core.exceptions import GraphError
from app.core.logger import get_logger
from app.modules.graph.model import EmployerEnrichmentInput, EmployerEnrichmentResult
from app.modules.graph.prompt_builder import build_employer_graph_user_prompt
from prompts.graph.employer_enrichment import EMPLOYER_GRAPH_SYSTEM_PROMPT
from app.modules.graph.schemas import employer_enrichment_parser
from app.modules.llm.interface import LLMMessage, LLMRequest
from app.modules.llm.router import LLMRouter

logger = get_logger(__name__)


def enrich_employer_with_llm(
    payload: EmployerEnrichmentInput,
    *,
    llm_router: LLMRouter,
    max_tokens: int = 1200,
) -> EmployerEnrichmentResult:
    has_company = bool(payload.company_description and payload.company_description.strip())
    has_job = bool(payload.job_description and payload.job_description.strip())

    if has_company and has_job:
        input_mode = "both"
    elif has_job:
        input_mode = "job"
    elif has_company:
        input_mode = "company"
    else:
        raise GraphError("Employer enrichment requires company_description and/or job_description.")

    user_prompt = build_employer_graph_user_prompt(
        company_name=payload.company_name,
        role=payload.role or "",
        company_description=payload.company_description or "",
        job_description=payload.job_description or "",
        input_mode=input_mode,
        format_instructions=employer_enrichment_parser.get_format_instructions(),
    )
    response = llm_router.generate(
        LLMRequest(
            messages=[
                LLMMessage(role="system", content=EMPLOYER_GRAPH_SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            temperature=0,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
    )
    parsed = employer_enrichment_parser.parse(response.content)
    logger.debug(
        "Enriched employer company=%s source=%s",
        payload.company_name,
        parsed.enrichment_source,
    )
    return EmployerEnrichmentResult(
        company_domains=parsed.company_domains,
        company_looked_for_capabilities=parsed.company_looked_for_capabilities,
        company_looked_for_technologies=parsed.company_looked_for_technologies,
        job_required_capabilities=parsed.job_required_capabilities,
        job_required_technologies=parsed.job_required_technologies,
        industry=parsed.industry,
        enrichment_source=parsed.enrichment_source,
    )
