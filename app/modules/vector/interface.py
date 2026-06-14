from __future__ import annotations

from typing import Any, Protocol


class VectorStore(Protocol):
    name: str

    def upsert(
        self,
        collection: str,
        *,
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        """Insert or update a vector point."""

    def search(
        self,
        collection: str,
        *,
        vector: list[float],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search nearest vectors."""

    def close(self) -> None:
        """Release underlying connections."""
