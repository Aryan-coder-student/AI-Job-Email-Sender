from __future__ import annotations

from typing import Any

from app.modules.mail.factory import build_default_mail_sender
from app.modules.mail.model import MailMessage
from app.modules.mail.sender import MailSender
from app.redis.config import RedisConfig
from app.redis.factory import build_default_email_draft_queue, build_rate_limiter
from app.redis.interface import EmailDraftQueue, RateLimiter


def run_process_email_queue(
    *,
    limit: int = 10,
    dry_run: bool = False,
    queue: EmailDraftQueue | None = None,
    rate_limiter: RateLimiter | None = None,
    sender: MailSender | None = None,
    config: RedisConfig | None = None,
) -> list[dict[str, Any]]:
    active_config = config or RedisConfig.from_env()
    active_queue = queue or build_default_email_draft_queue()
    active_rate_limiter = rate_limiter or build_rate_limiter(active_config)
    active_sender = sender
    results: list[dict[str, Any]] = []

    for draft in active_queue.fetch_pending(limit=limit):
        if not active_rate_limiter.allow(
            "email_send",
            limit=active_config.send_rate_limit,
            window_seconds=active_config.send_rate_window_seconds,
        ):
            results.append(
                {
                    "draft_id": draft.draft_id,
                    "to": draft.to,
                    "status": "rate_limited",
                }
            )
            break

        if dry_run:
            results.append(
                {
                    "draft_id": draft.draft_id,
                    "to": draft.to,
                    "status": "dry_run",
                }
            )
            continue

        if active_sender is None:
            active_sender = build_default_mail_sender()

        try:
            send_result = active_sender.send(
                MailMessage(
                    to=[draft.to],
                    subject=draft.subject,
                    body_text=draft.body_text,
                    body_html=draft.body_html,
                )
            )
            active_queue.mark_sent(draft.draft_id, message_id=send_result.message_id)
            results.append(
                {
                    "draft_id": draft.draft_id,
                    "to": draft.to,
                    "status": "sent",
                    "message_id": send_result.message_id,
                    "provider": send_result.provider,
                }
            )
        except Exception as error:
            active_queue.mark_failed(draft.draft_id, error=str(error))
            results.append(
                {
                    "draft_id": draft.draft_id,
                    "to": draft.to,
                    "status": "failed",
                    "error": str(error),
                }
            )

    return results
