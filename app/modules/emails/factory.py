from __future__ import annotations

from app.core.logger import get_logger
from app.modules.llm.factory import build_default_llm_router
from app.modules.llm.router import LLMRouter

logger = get_logger(__name__)


def build_draft_service(*, llm_router: LLMRouter | None = None) -> LLMRouter:
    router = llm_router or build_default_llm_router()
    logger.info("Initialized draft service")
    return router


def build_default_draft_service() -> LLMRouter:
    return build_draft_service()
