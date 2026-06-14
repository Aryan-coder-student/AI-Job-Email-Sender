from __future__ import annotations

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field


class EmailDraftSchema(BaseModel):
    subject: str = Field(min_length=1)
    body_text: str = Field(min_length=1)
    body_html: str | None = None


email_draft_parser = PydanticOutputParser(pydantic_object=EmailDraftSchema)
