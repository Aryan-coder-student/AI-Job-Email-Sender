from __future__ import annotations

from typing import Any
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from app.core.logger import get_logger
from app.modules.vector.config import VectorConfig

logger = get_logger(__name__)


class QdrantVectorStore:
    name = "qdrant"

    def __init__(self, config: VectorConfig) -> None:
        self.config = config
        self._client = QdrantClient(url=config.qdrant_url)
        self._ensure_collection(config.projects_collection, config.embedding_dimensions)
        self._ensure_collection(config.jobs_collection, config.embedding_dimensions)

    def upsert(
        self,
        collection: str,
        *,
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        self._ensure_collection(collection, len(vector))
        self._client.upsert(
            collection_name=collection,
            points=[
                PointStruct(
                    id=_point_uuid(point_id),
                    vector=vector,
                    payload={"point_id": point_id, **payload},
                )
            ],
        )

    def search(
        self,
        collection: str,
        *,
        vector: list[float],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        response = self._client.query_points(
            collection_name=collection,
            query=vector,
            limit=limit,
        )
        results: list[dict[str, Any]] = []
        for hit in response.points:
            payload = dict(hit.payload or {})
            payload["score"] = float(hit.score)
            results.append(payload)
        return results

    def close(self) -> None:
        self._client.close()

    def _ensure_collection(self, collection: str, dimensions: int) -> None:
        if self._client.collection_exists(collection):
            return
        logger.info("Creating Qdrant collection=%s dimensions=%s", collection, dimensions)
        self._client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=dimensions, distance=Distance.COSINE),
        )


def _point_uuid(point_id: str):
    return str(uuid5(NAMESPACE_URL, point_id))
