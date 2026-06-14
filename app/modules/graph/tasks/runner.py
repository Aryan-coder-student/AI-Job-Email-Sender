from __future__ import annotations

from pathlib import Path
from typing import Any

from app.modules.graph.builder import (
    build_candidate_graph,
    build_company_graph,
    enrich_github_profile,
    enrich_resume_profile,
)
from app.modules.graph.factory import build_default_graph_store
from app.modules.graph.serializers import (
    load_json_file,
    parsed_github_from_dict,
    parsed_resume_from_dict,
)
from app.modules.llm.factory import build_default_llm_router
from app.modules.vector.config import VectorConfig
from app.modules.vector.factory import (
    build_default_embedding_provider,
    build_default_vector_store,
)
from app.modules.vector.indexer import index_job_openings, index_projects


def run_build_knowledge_graph(
    *,
    resume: str | Path,
    github: str | Path,
    companies: str | Path,
    candidate_id: str | None = None,
    max_companies: int = 25,
    max_github_enrichment: int = 10,
    skip_enrichment: bool = False,
    clear: bool = False,
) -> dict[str, Any]:
    graph_store = build_default_graph_store()
    vector_store = build_default_vector_store()
    embedding_provider = build_default_embedding_provider()
    vector_config = VectorConfig.from_env()

    try:
        if clear:
            graph_store.clear()

        parsed_resume = parsed_resume_from_dict(load_json_file(str(resume)))
        parsed_github = parsed_github_from_dict(load_json_file(str(github)))
        company_records = load_json_file(str(companies))

        llm_router = None
        github_enrichments = None
        resume_enrichment = None
        if not skip_enrichment:
            llm_router = build_default_llm_router()
            github_enrichments = enrich_github_profile(
                parsed_github,
                llm_router=llm_router,
                max_projects=max_github_enrichment,
            )
            resume_enrichment = enrich_resume_profile(
                parsed_resume,
                parsed_github,
                llm_router=llm_router,
            )

        candidate_result = build_candidate_graph(
            parsed_resume=parsed_resume,
            parsed_github=parsed_github,
            graph_store=graph_store,
            github_enrichments=github_enrichments,
            resume_enrichment=resume_enrichment,
            candidate_id=candidate_id,
        )
        company_result = build_company_graph(
            company_records=company_records,
            graph_store=graph_store,
            llm_router=llm_router,
            max_records=max_companies,
        )
        projects_indexed = index_projects(
            parsed_github,
            vector_store=vector_store,
            embedding_provider=embedding_provider,
            collection=vector_config.projects_collection,
        )
        jobs_indexed = index_job_openings(
            company_records[:max_companies],
            vector_store=vector_store,
            embedding_provider=embedding_provider,
            collection=vector_config.jobs_collection,
        )
    finally:
        graph_store.close()
        vector_store.close()

    return {
        "candidate": candidate_result.to_dict(),
        "companies": company_result.to_dict(),
        "vector_index": {"projects_indexed": projects_indexed, "jobs_indexed": jobs_indexed},
    }
