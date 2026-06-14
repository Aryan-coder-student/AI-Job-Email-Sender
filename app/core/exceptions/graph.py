from __future__ import annotations

from app.core.exceptions.base import AppError


class GraphError(AppError):
    """Base error for knowledge graph operations."""


class GraphConfigurationError(GraphError):
    """Raised when graph/Neo4j configuration is missing or invalid."""


class GraphQueryError(GraphError):
    """Raised when a graph query fails."""
