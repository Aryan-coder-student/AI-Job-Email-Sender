from __future__ import annotations

from collections import defaultdict
from typing import Any

from neo4j import GraphDatabase, Session

from app.core.exceptions import GraphQueryError
from app.core.logger import get_logger
from app.modules.graph.config import GraphConfig
from app.modules.graph.model import (
    EmployerProfile,
    GraphEdge,
    GraphNode,
    MatchPath,
    ProjectMatch,
)

logger = get_logger(__name__)


class Neo4jGraphStore:
    name = "neo4j"

    def __init__(self, config: GraphConfig) -> None:
        self.config = config
        self._driver = GraphDatabase.driver(
            config.neo4j_uri,
            auth=(config.neo4j_user, config.neo4j_password),
        )

    def upsert_nodes(self, nodes: list[GraphNode]) -> int:
        if not nodes:
            return 0

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for node in nodes:
            grouped[node.label].append(
                {
                    "node_id": node.node_id,
                    "name": node.name,
                    "properties": {"node_id": node.node_id, "name": node.name, **node.properties},
                }
            )

        total = 0
        try:
            with self._session() as session:
                for label, payload in grouped.items():
                    query = f"""
                    UNWIND $nodes AS node
                    MERGE (n:{label} {{node_id: node.node_id}})
                    SET n += node.properties, n.name = node.name
                    RETURN count(n) AS count
                    """
                    result = session.run(query, nodes=payload).single()
                    total += int(result["count"]) if result else len(payload)
            return total
        except Exception as error:
            raise GraphQueryError(f"Failed to upsert nodes: {error}") from error

    def upsert_edges(self, edges: list[GraphEdge]) -> int:
        if not edges:
            return 0

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in edges:
            grouped[edge.relationship].append(
                {
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "properties": edge.properties,
                }
            )

        total = 0
        try:
            with self._session() as session:
                for relationship, payload in grouped.items():
                    query = f"""
                    UNWIND $edges AS edge
                    MATCH (source {{node_id: edge.source_id}})
                    MATCH (target {{node_id: edge.target_id}})
                    MERGE (source)-[r:{relationship}]->(target)
                    SET r += edge.properties
                    RETURN count(r) AS count
                    """
                    result = session.run(query, edges=payload).single()
                    total += int(result["count"]) if result else len(payload)
            return total
        except Exception as error:
            raise GraphQueryError(f"Failed to upsert edges: {error}") from error

    def clear(self) -> None:
        with self._session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def match_projects_for_employer(
        self,
        employer: EmployerProfile,
        *,
        candidate_id: str,
        limit: int = 10,
    ) -> tuple[list[ProjectMatch], list[MatchPath]]:
        use_job_paths = bool(employer.job_description or employer.role)
        company_id = employer.company_id
        job_id = employer.job_id

        job_query = """
        MATCH (job:JobOpening {node_id: $job_id})-[:REQUIRES]->(cap:Capability)<-[:DEMONSTRATES]-(project:Project)<-[:OWNS]-(candidate:Candidate {node_id: $candidate_id})
        RETURN project.node_id AS project_id, project.name AS project_name, cap.name AS capability, count(*) AS hits
        ORDER BY hits DESC
        LIMIT $limit
        """

        company_query = """
        MATCH (company:Company {node_id: $company_id})-[:LOOKS_FOR]->(cap:Capability)<-[:DEMONSTRATES]-(project:Project)<-[:OWNS]-(candidate:Candidate {node_id: $candidate_id})
        RETURN project.node_id AS project_id, project.name AS project_name, cap.name AS capability, count(*) AS hits
        ORDER BY hits DESC
        LIMIT $limit
        """

        domain_query = """
        MATCH (company:Company {node_id: $company_id})-[:OPERATES_IN]->(domain:Domain)<-[:BELONGS_TO]-(project:Project)<-[:OWNS]-(candidate:Candidate {node_id: $candidate_id})
        RETURN project.node_id AS project_id, project.name AS project_name, domain.name AS domain, count(*) AS hits
        ORDER BY hits DESC
        LIMIT $limit
        """

        job_tech_query = """
        MATCH (job:JobOpening {node_id: $job_id})-[:REQUIRES]->(tech:Technology)<-[:USES]-(project:Project)<-[:OWNS]-(candidate:Candidate {node_id: $candidate_id})
        RETURN project.node_id AS project_id, project.name AS project_name, tech.name AS capability, count(*) AS hits
        ORDER BY hits DESC
        LIMIT $limit
        """

        company_tech_query = """
        MATCH (company:Company {node_id: $company_id})-[:LOOKS_FOR]->(tech:Technology)<-[:USES]-(project:Project)<-[:OWNS]-(candidate:Candidate {node_id: $candidate_id})
        RETURN project.node_id AS project_id, project.name AS project_name, tech.name AS capability, count(*) AS hits
        ORDER BY hits DESC
        LIMIT $limit
        """

        project_scores: dict[str, dict[str, Any]] = {}
        paths: list[MatchPath] = []

        with self._session() as session:
            if use_job_paths and job_id:
                for record in session.run(
                    job_query,
                    job_id=job_id,
                    candidate_id=candidate_id,
                    limit=limit,
                ):
                    _accumulate_score(
                        project_scores,
                        paths,
                        record,
                        employer.company_name,
                        path_prefix=["JobOpening", "REQUIRES", record["capability"], "DEMONSTRATED_BY"],
                        weight=0.7,
                        match_source="job_capability",
                    )
                
                for record in session.run(
                    job_tech_query,
                    job_id=job_id,
                    candidate_id=candidate_id,
                    limit=limit,
                ):
                    _accumulate_score(
                        project_scores,
                        paths,
                        record,
                        employer.company_name,
                        path_prefix=["JobOpening", "REQUIRES", record["capability"], "USED_IN"],
                        weight=0.6,
                        match_source="job_technology",
                    )

            for record in session.run(
                company_query,
                company_id=company_id,
                candidate_id=candidate_id,
                limit=limit,
            ):
                weight = 0.3 if use_job_paths else 1.0
                _accumulate_score(
                    project_scores,
                    paths,
                    record,
                    employer.company_name,
                    path_prefix=["Company", "LOOKS_FOR", record["capability"], "DEMONSTRATED_BY"],
                    weight=weight,
                    match_source="company_capability",
                )

            for record in session.run(
                company_tech_query,
                company_id=company_id,
                candidate_id=candidate_id,
                limit=limit,
            ):
                weight = 0.3 if use_job_paths else 0.8
                _accumulate_score(
                    project_scores,
                    paths,
                    record,
                    employer.company_name,
                    path_prefix=["Company", "LOOKS_FOR", record["capability"], "USED_IN"],
                    weight=weight,
                    match_source="company_technology",
                )

            for record in session.run(
                domain_query,
                company_id=company_id,
                candidate_id=candidate_id,
                limit=limit,
            ):
                weight = 0.3 if use_job_paths else 0.5
                _accumulate_score(
                    project_scores,
                    paths,
                    record,
                    employer.company_name,
                    path_prefix=["Company", "OPERATES_IN", record["domain"], "BELONGS_TO"],
                    weight=weight,
                    match_source="domain",
                )

        matches = [
            ProjectMatch(
                project_id=project_id,
                project_name=data["project_name"],
                graph_score=min(data["score"], 1.0),
                embedding_score=0.0,
                llm_score=0.0,
                final_score=min(data["score"], 1.0),
                explanation="Graph overlap on shared capabilities/domains.",
                paths=[path for path in paths if path.project_name == data["project_name"]],
            )
            for project_id, data in sorted(
                project_scores.items(),
                key=lambda item: item[1]["score"],
                reverse=True,
            )[:limit]
        ]

        return matches, paths

    def close(self) -> None:
        self._driver.close()

    def _session(self) -> Session:
        return self._driver.session()


def _accumulate_score(
    project_scores: dict[str, dict[str, Any]],
    paths: list[MatchPath],
    record: Any,
    company_name: str,
    *,
    path_prefix: list[str],
    weight: float,
    match_source: str,
) -> None:
    project_id = record["project_id"]
    project_name = record["project_name"]
    hits = float(record["hits"])
    score_increment = min(hits / 5.0, 1.0) * weight

    if project_id not in project_scores:
        project_scores[project_id] = {"project_name": project_name, "score": 0.0}

    project_scores[project_id]["score"] += score_increment
    paths.append(
        MatchPath(
            company_name=company_name,
            project_name=project_name,
            path_labels=[*path_prefix, project_name],
            graph_score=score_increment,
            match_source=match_source,
        )
    )
