from __future__ import annotations

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import GROQ_API_KEY_FIELDS


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    log_level: str = "INFO"
    log_file: str | None = None

    groq_api_key_1: str = ""
    groq_api_key_2: str = ""
    groq_api_key_3: str = ""
    groq_api_key_4: str = ""
    groq_model: str = ""

    openai_api_key: str = ""
    openai_model: str = ""
    gemini_api_key: str = ""
    gemini_model: str = ""

    github_token: str = ""

    mail_provider: str = "gmail"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_timeout_seconds: int = 30

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_projects: str = "projects"
    qdrant_collection_jobs: str = "job_openings"

    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"

    hybrid_graph_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    hybrid_vector_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    hybrid_llm_weight: float = Field(default=0.3, ge=0.0, le=1.0)

    redis_url: str = "redis://localhost:6379/2"
    email_queue_key: str = "email:queue:pending"
    email_send_rate_limit: int = Field(default=10, ge=1)
    email_send_rate_window_seconds: int = Field(default=60, ge=1)

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    def groq_api_keys(self) -> list[str]:
        return [value for field in GROQ_API_KEY_FIELDS if (value := getattr(self, field))]


@lru_cache
def get_settings() -> Settings:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return Settings(_env_file=None)
    return Settings()


def reset_settings() -> None:
    get_settings.cache_clear()


def reload_settings() -> Settings:
    reset_settings()
    return get_settings()
