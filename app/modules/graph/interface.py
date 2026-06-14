from __future__ import annotations

from typing import Protocol

from app.modules.graph.model import (
    EmployerProfile,
    GraphEdge,
    GraphNode,
    MatchPath,
    ProjectMatch,
)


class GraphStore(Protocol):
    name: str

    def upsert_nodes(self, nodes: list[GraphNode]) -> int:
        """Insert or update graph nodes."""

    def upsert_edges(self, edges: list[GraphEdge]) -> int:
        """Insert or update graph edges."""

    def clear(self) -> None:
        """Remove all nodes and relationships."""

    def match_projects_for_employer(
        self,
        employer: EmployerProfile,
        *,
        candidate_id: str,
        limit: int = 10,
    ) -> tuple[list[ProjectMatch], list[MatchPath]]:
        """Return graph-scored project matches and explainable paths."""

    def close(self) -> None:
        """Release underlying connections."""
