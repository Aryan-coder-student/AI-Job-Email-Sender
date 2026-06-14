from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions import GraphConfigurationError
from app.core.settings import get_settings

DEFAULT_NEO4J_URI = "bolt://localhost:7687"
DEFAULT_NEO4J_USER = "neo4j"


@dataclass(frozen=True)
class GraphConfig:
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    hybrid_graph_weight: float = 0.4
    hybrid_vector_weight: float = 0.3
    hybrid_llm_weight: float = 0.3

    @classmethod
    def from_env(cls) -> GraphConfig:
        settings = get_settings()
        if not settings.neo4j_password.strip():
            raise GraphConfigurationError("NEO4J_PASSWORD is required.")

        return cls(
            neo4j_uri=settings.neo4j_uri or DEFAULT_NEO4J_URI,
            neo4j_user=settings.neo4j_user or DEFAULT_NEO4J_USER,
            neo4j_password=settings.neo4j_password,
            hybrid_graph_weight=settings.hybrid_graph_weight,
            hybrid_vector_weight=settings.hybrid_vector_weight,
            hybrid_llm_weight=settings.hybrid_llm_weight,
        )
