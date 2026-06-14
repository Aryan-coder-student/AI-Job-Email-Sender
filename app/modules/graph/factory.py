from __future__ import annotations

from app.core.logger import get_logger
from app.modules.graph.config import GraphConfig
from app.modules.graph.interface import GraphStore
from app.modules.graph.providers.neo4j import Neo4jGraphStore

logger = get_logger(__name__)


def build_graph_store(config: GraphConfig | None = None) -> GraphStore:
    active_config = config or GraphConfig.from_env()
    store = Neo4jGraphStore(active_config)
    logger.info("Initialized graph store provider=%s uri=%s", store.name, active_config.neo4j_uri)
    return store


def build_default_graph_store() -> GraphStore:
    return build_graph_store()
