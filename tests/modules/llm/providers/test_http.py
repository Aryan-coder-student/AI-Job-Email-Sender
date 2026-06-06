from __future__ import annotations

import json
from urllib.error import HTTPError, URLError

import pytest

from app.core.exceptions import LLMProviderError, LLMRateLimitError
from app.modules.llm.providers import http


class FakeHeaders:
    def __init__(self, values: dict[str, str]) -> None:
        self.values = values

    def items(self):
        return self.values.items()

    def get(self, key: str) -> str | None:
        return self.values.get(key)


class FakeResponse:
    def __init__(self, body: str, headers: dict[str, str] | None = None) -> None:
        self.body = body
        self.headers = FakeHeaders(headers or {})

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body.encode("utf-8")

    def close(self) -> None:
        return None


def test_post_json_returns_response_and_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout: int) -> FakeResponse:
        assert request.full_url == "https://example.com"
        assert timeout == 10
        assert json.loads(request.data.decode("utf-8")) == {"hello": "world"}
        return FakeResponse('{"ok": true}', headers={"x-test": "yes"})

    monkeypatch.setattr(http, "urlopen", fake_urlopen)

    response, headers = http.post_json(
        url="https://example.com",
        headers={"Authorization": "Bearer key"},
        payload={"hello": "world"},
        provider="test",
        timeout_seconds=10,
    )

    assert response == {"ok": True}
    assert headers == {"x-test": "yes"}


def test_post_json_wraps_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout: int) -> FakeResponse:
        raise HTTPError(
            url="https://example.com",
            code=429,
            msg="Too Many Requests",
            hdrs=FakeHeaders({"retry-after": "3"}),
            fp=FakeResponse('{"error": "rate"}'),
        )

    monkeypatch.setattr(http, "urlopen", fake_urlopen)

    with pytest.raises(LLMRateLimitError) as error:
        http.post_json(
            url="https://example.com",
            headers={},
            payload={},
            provider="test",
            timeout_seconds=10,
        )

    assert error.value.retry_after_seconds == 3


def test_post_json_wraps_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout: int) -> FakeResponse:
        raise HTTPError(
            url="https://example.com",
            code=500,
            msg="Server Error",
            hdrs=FakeHeaders({}),
            fp=FakeResponse("broken"),
        )

    monkeypatch.setattr(http, "urlopen", fake_urlopen)

    with pytest.raises(LLMProviderError, match="HTTP 500"):
        http.post_json(
            url="https://example.com",
            headers={},
            payload={},
            provider="test",
            timeout_seconds=10,
        )


def test_post_json_wraps_url_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout: int) -> FakeResponse:
        raise URLError("offline")

    monkeypatch.setattr(http, "urlopen", fake_urlopen)

    with pytest.raises(LLMProviderError, match="offline"):
        http.post_json(
            url="https://example.com",
            headers={},
            payload={},
            provider="test",
            timeout_seconds=10,
        )


def test_post_json_wraps_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        http,
        "urlopen",
        lambda request, timeout: FakeResponse("not json"),
    )

    with pytest.raises(LLMProviderError, match="invalid JSON"):
        http.post_json(
            url="https://example.com",
            headers={},
            payload={},
            provider="test",
            timeout_seconds=10,
        )


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, None), ("", None), ("2", 2), ("2.5", 2), ("bad", None)],
)
def test_parse_retry_after(value: str | None, expected: int | None) -> None:
    assert http._parse_retry_after(value) == expected
