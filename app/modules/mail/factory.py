from __future__ import annotations

from app.core.logger import get_logger
from app.modules.mail.config import MailConfig
from app.modules.mail.providers.smtp import SmtpMailProvider
from app.modules.mail.sender import MailSender

logger = get_logger(__name__)


def build_mail_sender(config: MailConfig | None = None) -> MailSender:
    active_config = config or MailConfig.from_env()
    provider = SmtpMailProvider(active_config)
    logger.info(
        "Initialized mail sender provider=%s host=%s port=%s",
        provider.name,
        active_config.host,
        active_config.port,
    )
    return MailSender(provider)


def build_default_mail_sender() -> MailSender:
    return build_mail_sender()
