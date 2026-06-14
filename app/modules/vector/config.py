from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions import VectorConfigurationError
from app.core.settings import get_settings

DEFAULT_QDRANT_URL = "http://localhost:6333"
DEFAULT_EMBEDDING_PROVIDER = "openai"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_PROJECTS_COLLECTION = "projects"
DEFAULT_JOBS_COLLECTION = "job_openings"


@dataclass(frozen=True)
class VectorConfig:
    qdrant_url: str
    projects_collection: str
    jobs_collection: str
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int = 1536

    @classmethod
    def from_env(cls) -> VectorConfig:
        settings = get_settings()
        return cls(
            qdrant_url=settings.qdrant_url or DEFAULT_QDRANT_URL,
            projects_collection=settings.qdrant_collection_projects or DEFAULT_PROJECTS_COLLECTION,
            jobs_collection=settings.qdrant_collection_jobs or DEFAULT_JOBS_COLLECTION,
            embedding_provider=(settings.embedding_provider or DEFAULT_EMBEDDING_PROVIDER).lower(),
            embedding_model=settings.embedding_model or DEFAULT_EMBEDDING_MODEL,
        )

    def validate(self) -> None:
        if self.embedding_provider not in {"openai", "gemini", "local"}:
            raise VectorConfigurationError(
                "EMBEDDING_PROVIDER must be openai, gemini, or local."
            )
