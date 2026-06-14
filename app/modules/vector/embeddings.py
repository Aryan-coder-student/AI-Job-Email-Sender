from __future__ import annotations

import hashlib
from typing import Protocol

from app.core.exceptions import VectorConfigurationError
from app.modules.vector.config import VectorConfig
from app.core.settings import get_settings


class EmbeddingProvider(Protocol):
    name: str

    def embed(self, text: str) -> list[float]:
        """Return an embedding vector for text."""


class OpenAIEmbeddingProvider:
    name = "openai"

    def __init__(self, config: VectorConfig) -> None:
        from langchain_openai import OpenAIEmbeddings

        api_key = get_settings().openai_api_key
        if not api_key:
            raise VectorConfigurationError("OPENAI_API_KEY is required for OpenAI embeddings.")
        self._client = OpenAIEmbeddings(model=config.embedding_model, api_key=api_key)

    def embed(self, text: str) -> list[float]:
        return self._client.embed_query(text)


class GeminiEmbeddingProvider:
    name = "gemini"

    def __init__(self, config: VectorConfig) -> None:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        api_key = get_settings().gemini_api_key
        if not api_key:
            raise VectorConfigurationError("GEMINI_API_KEY is required for Gemini embeddings.")
        self._client = GoogleGenerativeAIEmbeddings(model=config.embedding_model, google_api_key=api_key)

    def embed(self, text: str) -> list[float]:
        return self._client.embed_query(text)


class LocalHashEmbeddingProvider:
    """Deterministic local embeddings for dev/testing without external API keys."""

    name = "local"

    def __init__(self, config: VectorConfig) -> None:
        self._dimensions = config.embedding_dimensions

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        seed = digest

        while len(values) < self._dimensions:
            for byte in seed:
                values.append((byte / 127.5) - 1.0)
                if len(values) >= self._dimensions:
                    break
            seed = hashlib.sha256(seed).digest()

        return values


def build_embedding_provider(config: VectorConfig) -> EmbeddingProvider:
    config.validate()
    if config.embedding_provider == "openai":
        return OpenAIEmbeddingProvider(config)
    if config.embedding_provider == "gemini":
        return GeminiEmbeddingProvider(config)
    return LocalHashEmbeddingProvider(config)


def stable_point_id(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"
