from __future__ import annotations

from app.modules.emails.model import EmailDraft
from app.redis.config import RedisConfig
from app.redis.queues.email_draft import RedisEmailDraftQueue
from tests.redis.fakes import FakeRedis


def build_queue(client: FakeRedis | None = None) -> RedisEmailDraftQueue:
    config = RedisConfig(
        redis_url="redis://localhost:6379/2",
        email_queue_key="email:queue:pending",
        send_rate_limit=10,
        send_rate_window_seconds=60,
    )
    return RedisEmailDraftQueue(config, client or FakeRedis())


def build_draft(*, draft_id: str = "draft-1") -> EmailDraft:
    return EmailDraft(
        draft_id=draft_id,
        to="hr@acme.com",
        subject="Application",
        body_text="Hello",
        company_name="Acme",
        project_name="demo",
    )
