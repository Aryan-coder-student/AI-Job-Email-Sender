from __future__ import annotations

import json
from typing import Any

from app.core.exceptions import RedisOperationError
from app.core.logger import get_logger
from app.modules.emails.model import EmailDraft, EnqueueResult
from app.redis.config import RedisConfig
from app.redis.interface import RedisClient

logger = get_logger(__name__)


class RedisEmailDraftQueue:
    def __init__(self, config: RedisConfig, client: RedisClient) -> None:
        self.config = config
        self._client = client

    @property
    def queue_key(self) -> str:
        return self.config.email_queue_key

    def _draft_key(self, draft_id: str) -> str:
        return f"email:draft:{draft_id}"

    def enqueue(self, draft: EmailDraft) -> EnqueueResult:
        queued_draft = draft.with_status("queued")
        payload = json.dumps(queued_draft.to_dict(), ensure_ascii=False)

        try:
            self._client.set(self._draft_key(draft.draft_id), payload)
            self._client.rpush(self.queue_key, draft.draft_id)
        except RedisOperationError as error:
            raise RedisOperationError(f"Failed to enqueue draft {draft.draft_id}: {error}") from error

        logger.info("Enqueued email draft draft_id=%s to=%s", draft.draft_id, draft.to)
        return EnqueueResult(draft_id=draft.draft_id, queue_key=self.queue_key)

    def get(self, draft_id: str) -> EmailDraft | None:
        try:
            payload = self._client.get(self._draft_key(draft_id))
        except RedisOperationError as error:
            raise RedisOperationError(f"Failed to fetch draft {draft_id}: {error}") from error

        if not payload:
            return None

        return EmailDraft.from_dict(json.loads(payload))

    def fetch_pending(self, limit: int = 10) -> list[EmailDraft]:
        if limit < 1:
            return []

        try:
            draft_ids = self._client.lrange(self.queue_key, 0, limit - 1)
        except RedisOperationError as error:
            raise RedisOperationError(f"Failed to fetch pending drafts: {error}") from error

        drafts: list[EmailDraft] = []
        for draft_id in draft_ids:
            draft = self.get(draft_id)
            if draft is None or draft.status != "queued":
                continue
            drafts.append(draft)

        return drafts

    def mark_sent(self, draft_id: str, *, message_id: str | None = None) -> EmailDraft:
        return self._update_status(draft_id, "sent", message_id=message_id)

    def mark_failed(self, draft_id: str, *, error: str) -> EmailDraft:
        return self._update_status(draft_id, "failed", error=error)

    def remove_from_queue(self, draft_id: str) -> None:
        try:
            self._client.lrem(self.queue_key, 1, draft_id)
        except RedisOperationError as error:
            raise RedisOperationError(f"Failed to remove draft {draft_id} from queue: {error}") from error

    def _update_status(self, draft_id: str, status: str, **metadata: Any) -> EmailDraft:
        draft = self.get(draft_id)
        if draft is None:
            raise RedisOperationError(f"Draft not found: {draft_id}")

        updated = draft.with_status(status, **metadata)
        payload = json.dumps(updated.to_dict(), ensure_ascii=False)

        try:
            self._client.set(self._draft_key(draft_id), payload)
            if status in {"sent", "failed"}:
                self.remove_from_queue(draft_id)
        except RedisOperationError as error:
            raise RedisOperationError(f"Failed to update draft {draft_id}: {error}") from error

        return updated
