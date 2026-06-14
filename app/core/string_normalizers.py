from __future__ import annotations

from typing import Any


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def string_or_none(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()

    return None


def string_or_empty(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()

    return ""
