from __future__ import annotations

import asyncio
from urllib.error import HTTPError, URLError

import pytest

from app.core.exceptions import InvalidExcelError
from app.modules.excel.config import ExcelParserConfig
from app.modules.excel import sources


class FakeUploadFile:
    filename = "companies.xlsx"

    async def read(self) -> bytes:
        return b"excel-bytes"


class FakeResponse:
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        if not self.chunks:
            return b""

        return self.chunks.pop(0)


def test_parse_excel_from_fastapi_upload_delegates_to_upload_parser(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, object] = {}
    expected = object()
    config = ExcelParserConfig()

    def fake_parse_excel_from_upload(
        file_content: bytes,
        filename: str | None = None,
        config: ExcelParserConfig | None = None,
    ) -> object:
        calls["file_content"] = file_content
        calls["filename"] = filename
        calls["config"] = config
        return expected

    monkeypatch.setattr(sources, "parse_excel_from_upload", fake_parse_excel_from_upload)

    result = asyncio.run(sources.parse_excel_from_fastapi_upload(FakeUploadFile(), config))

    assert result is expected
    assert calls == {
        "file_content": b"excel-bytes",
        "filename": "companies.xlsx",
        "config": config,
    }


def test_parse_excel_from_url_downloads_and_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, object] = {}
    expected = object()
    config = ExcelParserConfig()

    monkeypatch.setattr(sources, "_download_excel", lambda url, config: b"excel-bytes")

    def fake_parse_excel_from_upload(
        file_content: bytes,
        filename: str | None = None,
        config: ExcelParserConfig | None = None,
    ) -> object:
        calls["file_content"] = file_content
        calls["filename"] = filename
        calls["config"] = config
        return expected

    monkeypatch.setattr(sources, "parse_excel_from_upload", fake_parse_excel_from_upload)

    result = sources.parse_excel_from_url("https://example.com/files/companies.xlsx", config)

    assert result is expected
    assert calls == {
        "file_content": b"excel-bytes",
        "filename": "companies.xlsx",
        "config": config,
    }


def test_parse_excel_from_url_converts_google_sheet_links(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, object] = {}
    expected = object()
    google_sheet_url = (
        "https://docs.google.com/spreadsheets/d/sheet-id/htmlview#gid=1279011369"
    )

    def fake_download_excel(url: str, config: ExcelParserConfig) -> bytes:
        calls["download_url"] = url
        return b"excel-bytes"

    def fake_parse_excel_from_upload(
        file_content: bytes,
        filename: str | None = None,
        config: ExcelParserConfig | None = None,
    ) -> object:
        calls["file_content"] = file_content
        calls["filename"] = filename
        calls["config"] = config
        return expected

    monkeypatch.setattr(sources, "_download_excel", fake_download_excel)
    monkeypatch.setattr(sources, "parse_excel_from_upload", fake_parse_excel_from_upload)

    result = sources.parse_excel_from_url(google_sheet_url, ExcelParserConfig())

    assert result is expected
    assert calls == {
        "download_url": (
            "https://docs.google.com/spreadsheets/d/sheet-id/export"
            "?format=xlsx&gid=1279011369"
        ),
        "file_content": b"excel-bytes",
        "filename": "google-sheet-sheet-id.xlsx",
        "config": ExcelParserConfig(),
    }


def test_parse_excel_from_path_reads_file_and_delegates(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    calls: dict[str, object] = {}
    expected = object()
    file_path = tmp_path / "companies.xlsx"
    file_path.write_bytes(b"excel-bytes")

    def fake_parse_excel_from_upload(
        file_content: bytes,
        filename: str | None = None,
        config: ExcelParserConfig | None = None,
    ) -> object:
        calls["file_content"] = file_content
        calls["filename"] = filename
        calls["config"] = config
        return expected

    monkeypatch.setattr(sources, "parse_excel_from_upload", fake_parse_excel_from_upload)

    result = sources.parse_excel_from_path(file_path)

    assert result is expected
    assert calls == {
        "file_content": b"excel-bytes",
        "filename": "companies.xlsx",
        "config": None,
    }


def test_parse_excel_from_path_wraps_read_errors(tmp_path) -> None:
    missing_file = tmp_path / "missing.xlsx"

    with pytest.raises(InvalidExcelError, match="Could not read Excel file"):
        sources.parse_excel_from_path(missing_file)


def test_download_excel_reads_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout: int) -> FakeResponse:
        assert request.full_url == "https://example.com/companies.xlsx"
        assert timeout == 20
        return FakeResponse([b"abc", b"def"])

    monkeypatch.setattr(sources, "urlopen", fake_urlopen)

    content = sources._download_excel(
        "https://example.com/companies.xlsx",
        ExcelParserConfig(),
    )

    assert content == b"abcdef"


def test_download_excel_converts_google_sheet_url_before_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request, timeout: int) -> FakeResponse:
        assert request.full_url == (
            "https://docs.google.com/spreadsheets/d/sheet-id/export"
            "?format=xlsx&gid=7"
        )
        return FakeResponse([b"excel-bytes"])

    monkeypatch.setattr(sources, "urlopen", fake_urlopen)

    content = sources._download_excel(
        "https://docs.google.com/spreadsheets/d/sheet-id/edit#gid=7",
        ExcelParserConfig(),
    )

    assert content == b"excel-bytes"


def test_download_excel_rejects_large_files(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sources,
        "urlopen",
        lambda request, timeout: FakeResponse([b"12", b"34"]),
    )

    with pytest.raises(InvalidExcelError, match="larger than the configured download limit"):
        sources._download_excel(
            "https://example.com/companies.xlsx",
            ExcelParserConfig(max_download_bytes=3),
        )


def test_download_excel_wraps_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout: int) -> None:
        raise HTTPError(
            url="https://example.com/companies.xlsx",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(sources, "urlopen", fake_urlopen)

    with pytest.raises(InvalidExcelError, match="HTTP 404"):
        sources._download_excel("https://example.com/companies.xlsx", ExcelParserConfig())


def test_download_excel_wraps_url_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout: int) -> None:
        raise URLError("offline")

    monkeypatch.setattr(sources, "urlopen", fake_urlopen)

    with pytest.raises(InvalidExcelError, match="offline"):
        sources._download_excel("https://example.com/companies.xlsx", ExcelParserConfig())


def test_download_excel_rejects_invalid_url_before_network() -> None:
    with pytest.raises(InvalidExcelError, match="Excel URL must start"):
        sources._download_excel("file:///tmp/companies.xlsx", ExcelParserConfig())


def test_filename_from_url() -> None:
    assert sources._filename_from_url("https://example.com/files/companies.xlsx") == (
        "companies.xlsx"
    )
    assert sources._filename_from_url(
        "https://docs.google.com/spreadsheets/d/sheet-id/htmlview#gid=1"
    ) == "google-sheet-sheet-id.xlsx"
    assert sources._filename_from_url("https://example.com") is None


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://docs.google.com/spreadsheets/d/sheet-id/htmlview#gid=1279011369",
            (
                "https://docs.google.com/spreadsheets/d/sheet-id/export"
                "?format=xlsx&gid=1279011369"
            ),
        ),
        (
            "https://docs.google.com/spreadsheets/d/sheet-id/edit?gid=5",
            "https://docs.google.com/spreadsheets/d/sheet-id/export?format=xlsx&gid=5",
        ),
        (
            "https://docs.google.com/spreadsheets/d/sheet-id/export?format=xlsx",
            "https://docs.google.com/spreadsheets/d/sheet-id/export?format=xlsx",
        ),
        (
            "https://example.com/companies.xlsx",
            "https://example.com/companies.xlsx",
        ),
    ],
)
def test_normalize_excel_download_url(url: str, expected: str) -> None:
    assert sources._normalize_excel_download_url(url) == expected
