from __future__ import annotations

from app.core.logger import get_logger
from app.modules.vector.config import VectorConfig
from app.modules.vector.embeddings import EmbeddingProvider, build_embedding_provider
from app.modules.vector.interface import VectorStore
from app.modules.vector.providers.qdrant import QdrantVectorStore

logger = get_logger(__name__)


def build_vector_store(config: VectorConfig | None = None) -> VectorStore:
    active_config = config or VectorConfig.from_env()
    store = QdrantVectorStore(active_config)
    logger.info("Initialized vector store provider=%s url=%s", store.name, active_config.qdrant_url)
    return store


def build_default_vector_store() -> VectorStore:
    return build_vector_store()


def build_default_embedding_provider(config: VectorConfig | None = None) -> EmbeddingProvider:
    active_config = config or VectorConfig.from_env()
    return build_embedding_provider(active_config)
