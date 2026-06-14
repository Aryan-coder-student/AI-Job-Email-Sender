from __future__ import annotations

import json

from tests.redis.helpers import build_draft, build_queue


def test_enqueue_and_fetch_pending() -> None:
    queue = build_queue()
    draft = build_draft()

    result = queue.enqueue(draft)
    assert result.draft_id == "draft-1"

    pending = queue.fetch_pending(limit=5)
    assert len(pending) == 1
    assert pending[0].status == "queued"
    assert pending[0].subject == "Application"


def test_mark_sent_removes_from_queue() -> None:
    queue = build_queue()
    queue.enqueue(build_draft(draft_id="draft-2"))

    updated = queue.mark_sent("draft-2", message_id="msg-1")
    assert updated.status == "sent"
    assert updated.metadata["message_id"] == "msg-1"
    assert queue.fetch_pending(limit=5) == []


def test_mark_failed_updates_status() -> None:
    queue = build_queue()
    queue.enqueue(build_draft(draft_id="draft-3"))

    updated = queue.mark_failed("draft-3", error="smtp down")
    assert updated.status == "failed"
    assert updated.metadata["error"] == "smtp down"

    stored = queue.get("draft-3")
    assert stored is not None
    assert stored.status == "failed"
    assert json.loads(json.dumps(stored.to_dict()))["status"] == "failed"
