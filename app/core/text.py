from __future__ import annotations

import re


def clean_document_text(raw_text: str) -> str:
    text = raw_text.replace("\x00", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate_document_text(raw_text: str, max_chars: int) -> str:
    cleaned_text = clean_document_text(raw_text)

    if len(cleaned_text) <= max_chars:
        return cleaned_text

    return cleaned_text[:max_chars].rstrip()
