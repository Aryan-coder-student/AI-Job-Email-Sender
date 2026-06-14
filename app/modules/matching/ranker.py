from __future__ import annotations

import json
import re
from typing import Any

from app.core.logger import get_logger
from app.modules.graph.config import GraphConfig
from app.modules.graph.factory import build_default_graph_store
from app.modules.graph.interface import GraphStore
from app.modules.graph.model import EmployerProfile, MatchPath, ProjectMatch
from app.modules.graph.normalizer import build_company_id, build_job_id
from app.modules.llm.interface import LLMMessage, LLMRequest
from app.modules.llm.router import LLMRouter
from app.modules.vector.config import VectorConfig
from app.modules.vector.embeddings import EmbeddingProvider
from app.modules.vector.factory import (
    build_default_embedding_provider,
    build_default_vector_store,
)
from app.modules.vector.indexer import build_employer_embedding_text
from app.modules.vector.interface import VectorStore

logger = get_logger(__name__)


def rank_projects_for_employer(
    *,
    company_record: dict[str, Any],
    candidate_id: str,
    graph_store: GraphStore | None = None,
    vector_store: VectorStore | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    llm_router: LLMRouter | None = None,
    graph_config: GraphConfig | None = None,
    vector_config: VectorConfig | None = None,
    limit: int = 5,
) -> list[ProjectMatch]:
    active_graph_config = graph_config or GraphConfig.from_env()
    active_vector_config = vector_config or VectorConfig.from_env()
    owns_graph_store = graph_store is None
    owns_vector_store = vector_store is None
    graph_store = graph_store or build_default_graph_store()
    vector_store = vector_store or build_default_vector_store()
    embedding_provider = embedding_provider or build_default_embedding_provider(active_vector_config)

    try:
        employer = _build_employer_profile(company_record)
        graph_matches, paths = graph_store.match_projects_for_employer(
            employer,
            candidate_id=candidate_id,
            limit=limit,
        )
        graph_scores = {match.project_id: match.graph_score for match in graph_matches}
        vector_scores, vector_hits = _search_project_vectors(
            company_record=company_record,
            vector_store=vector_store,
            embedding_provider=embedding_provider,
            vector_config=active_vector_config,
            limit=limit,
        )

        ranked: list[ProjectMatch] = []
        for project_id in _merge_project_ids(graph_scores, vector_scores)[: limit * 2]:
            graph_score = graph_scores.get(project_id, 0.0)
            embedding_score = vector_scores.get(project_id, 0.0)
            project_name = _project_name_from_hits(project_id, graph_matches, vector_hits)
            project_paths = [path for path in paths if path.project_name == project_name]
            llm_score, explanation = _score_with_llm(
                company_record=company_record,
                project_name=project_name,
                graph_score=graph_score,
                embedding_score=embedding_score,
                paths=project_paths,
                llm_router=llm_router,
            )
            final_score = (
                graph_score * active_graph_config.hybrid_graph_weight
                + embedding_score * active_graph_config.hybrid_vector_weight
                + llm_score * active_graph_config.hybrid_llm_weight
            )
            ranked.append(
                ProjectMatch(
                    project_id=project_id,
                    project_name=project_name,
                    graph_score=graph_score,
                    embedding_score=embedding_score,
                    llm_score=llm_score,
                    final_score=final_score,
                    explanation=explanation,
                    paths=project_paths,
                )
            )

        ranked.sort(key=lambda item: item.final_score, reverse=True)
        return ranked[:limit]
    finally:
        if owns_graph_store:
            graph_store.close()
        if owns_vector_store:
            vector_store.close()


def _build_employer_profile(company_record: dict[str, Any]) -> EmployerProfile:
    company_name = str(company_record.get("company_name") or "")
    company_id = build_company_id(
        company_name=company_name,
        company_url=company_record.get("company_url"),
    )
    return EmployerProfile(
        company_id=company_id,
        company_name=company_name,
        company_description=company_record.get("company_description"),
        job_description=company_record.get("job_description"),
        role=company_record.get("role"),
        job_id=build_job_id(
            company_id=company_id,
            job_url=company_record.get("job_url"),
            source_row=company_record.get("source_row"),
        ),
    )


def _search_project_vectors(
    *,
    company_record: dict[str, Any],
    vector_store: VectorStore,
    embedding_provider: EmbeddingProvider,
    vector_config: VectorConfig,
    limit: int,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    employer_text = build_employer_embedding_text(
        company_description=company_record.get("company_description"),
        job_description=company_record.get("job_description"),
        role=company_record.get("role"),
    )
    employer_vector = embedding_provider.embed(employer_text)
    vector_hits = vector_store.search(
        vector_config.projects_collection,
        vector=employer_vector,
        limit=limit * 2,
    )
    vector_scores = {
        str(hit.get("project_id") or hit.get("point_id")): float(hit.get("score", 0.0))
        for hit in vector_hits
    }
    return vector_scores, vector_hits


def _merge_project_ids(graph_scores: dict[str, float], vector_scores: dict[str, float]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for project_id in sorted(graph_scores, key=lambda item: graph_scores[item], reverse=True):
        if project_id not in seen:
            ordered.append(project_id)
            seen.add(project_id)
    for project_id in sorted(vector_scores, key=lambda item: vector_scores[item], reverse=True):
        if project_id not in seen:
            ordered.append(project_id)
            seen.add(project_id)
    return ordered


def _project_name_from_hits(
    project_id: str,
    graph_matches: list[ProjectMatch],
    vector_hits: list[dict[str, Any]],
) -> str:
    for match in graph_matches:
        if match.project_id == project_id:
            return match.project_name
    for hit in vector_hits:
        if str(hit.get("project_id") or hit.get("point_id")) == project_id:
            return str(hit.get("repo_name") or project_id)
    return project_id


def _score_with_llm(
    *,
    company_record: dict[str, Any],
    project_name: str,
    graph_score: float,
    embedding_score: float,
    paths: list[MatchPath],
    llm_router: LLMRouter | None,
) -> tuple[float, str]:
    if llm_router is None:
        source = "job requirements" if company_record.get("job_description") else "company context"
        return 0.5, f"Matched via graph/vector overlap using {source}."

    prompt = f"""
Score candidate project fit from 0 to 1.
Company: {company_record.get("company_name")}
Company description: {company_record.get("company_description")}
Job description: {company_record.get("job_description")}
Role: {company_record.get("role")}
Project: {project_name}
Graph score: {graph_score:.2f}
Embedding score: {embedding_score:.2f}
Graph paths: {json.dumps([path.to_dict() for path in paths], ensure_ascii=False)}

Return JSON with keys: score (float 0-1), reason (string citing JD or company context).
""".strip()
    response = llm_router.generate(
        LLMRequest(
            messages=[
                LLMMessage(role="system", content="You rank project-company fit concisely."),
                LLMMessage(role="user", content=prompt),
            ],
            temperature=0,
            max_tokens=300,
            response_format={"type": "json_object"},
        )
    )
    try:
        payload = json.loads(response.content)
        score = float(payload.get("score", 0.5))
        reason = str(payload.get("reason") or "LLM fit score generated.")
        return max(0.0, min(score, 1.0)), reason
    except (TypeError, ValueError, json.JSONDecodeError):
        match = re.search(r"0\.\d+|1\.0|1", response.content)
        score = float(match.group()) if match else 0.5
        return score, response.content.strip()[:240]
