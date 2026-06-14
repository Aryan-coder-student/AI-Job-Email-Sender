from __future__ import annotations

from app.modules.mail.model import MailMessage, SendMailResult
from app.modules.mail.sender import MailSender


class FakeMailProvider:
    name = "fake"

    def __init__(self) -> None:
        self.messages: list[MailMessage] = []

    def send(self, message: MailMessage) -> SendMailResult:
        self.messages.append(message)
        return SendMailResult(
            provider=self.name,
            recipients=message.to,
            message_id="test-message-id",
        )


def test_mail_sender_validates_and_delegates_to_provider() -> None:
    provider = FakeMailProvider()
    sender = MailSender(provider)

    result = sender.send(
        MailMessage(
            to=["hr@acme.com"],
            subject="Application",
            body_text="Hello",
        )
    )

    assert result.message_id == "test-message-id"
    assert len(provider.messages) == 1
    assert provider.messages[0].subject == "Application"
