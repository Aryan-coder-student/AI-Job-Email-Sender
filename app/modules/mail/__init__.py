from app.modules.mail.factory import build_default_mail_sender, build_mail_sender
from app.modules.mail.model import MailAttachment, MailMessage, SendMailResult
from app.modules.mail.sender import MailSender

__all__ = [
    "MailAttachment",
    "MailMessage",
    "MailSender",
    "SendMailResult",
    "build_default_mail_sender",
    "build_mail_sender",
]
