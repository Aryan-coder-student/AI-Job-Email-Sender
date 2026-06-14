from __future__ import annotations

import pytest

from app.core.settings import reset_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    reset_settings()
    yield
    reset_settings()
