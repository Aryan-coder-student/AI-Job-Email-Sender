from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

from app.core.exceptions import InvalidExcelError
from app.core.logger import get_logger
from app.modules.excel.config import ExcelParserConfig
from app.modules.excel.parser import ParsedExcelWorkbook, parse_excel_from_upload
from app.modules.excel.validator import validate_excel_url

logger = get_logger(__name__)


async def parse_excel_from_fastapi_upload(
    upload_file: Any,
    config: ExcelParserConfig | None = None,
) -> ParsedExcelWorkbook:
    """Read a FastAPI UploadFile-like object and parse it as an Excel workbook."""
    filename = getattr(upload_file, "filename", None)
    file_content = await upload_file.read()
    return parse_excel_from_upload(file_content, filename=filename, config=config)


def parse_excel_from_url(
    url: str,
    config: ExcelParserConfig | None = None,
) -> ParsedExcelWorkbook:
    """Download an Excel file from an HTTP or HTTPS URL and parse it."""
    active_config = config or ExcelParserConfig()
    active_config.validate()

    download_url = _normalize_excel_download_url(url)
    logger.info("Downloading Excel file url=%s", download_url)
    file_content = _download_excel(download_url, active_config)
    filename = _filename_from_url(url)
    logger.info(
        "Downloaded Excel file url=%s bytes=%s filename=%s",
        download_url,
        len(file_content),
        filename,
    )
    return parse_excel_from_upload(
        file_content=file_content,
        filename=filename,
        config=active_config,
    )


def parse_excel_from_path(
    path: str | Path,
    config: ExcelParserConfig | None = None,
) -> ParsedExcelWorkbook:
    """Read a local Excel file from disk and parse it."""
    file_path = Path(path)
    logger.info("Parsing Excel file from path=%s", file_path)

    try:
        file_content = file_path.read_bytes()
    except OSError as error:
        logger.exception("Could not read Excel file path=%s", file_path)
        raise InvalidExcelError(f"Could not read Excel file: {error}") from error

    return parse_excel_from_upload(
        file_content=file_content,
        filename=file_path.name,
        config=config,
    )


def _download_excel(url: str, config: ExcelParserConfig) -> bytes:
    download_url = _normalize_excel_download_url(url)
    validate_excel_url(download_url)

    request = Request(download_url, headers={"User-Agent": "job-send-crawl/1.0"})

    try:
        with urlopen(request, timeout=config.download_timeout_seconds) as response:
            chunks: list[bytes] = []
            total_bytes = 0

            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break

                total_bytes += len(chunk)
                if total_bytes > config.max_download_bytes:
                    raise InvalidExcelError(
                        "Excel file is larger than the configured download limit."
                    )

                chunks.append(chunk)

            return b"".join(chunks)
    except HTTPError as error:
        logger.warning("Excel download failed url=%s status=%s", download_url, error.code)
        raise InvalidExcelError(f"Could not download Excel file: HTTP {error.code}") from error
    except URLError as error:
        logger.warning("Excel download failed url=%s reason=%s", download_url, error.reason)
        raise InvalidExcelError(f"Could not download Excel file: {error.reason}") from error


def _normalize_excel_download_url(url: str) -> str:
    parsed_url = urlparse(url)
    spreadsheet_id = _google_spreadsheet_id(parsed_url.path)

    if parsed_url.netloc != "docs.google.com" or spreadsheet_id is None:
        return url

    query_params = {"format": "xlsx"}
    gid = _google_sheet_gid(parsed_url.query, parsed_url.fragment)

    if gid:
        query_params["gid"] = gid

    return urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            f"/spreadsheets/d/{spreadsheet_id}/export",
            "",
            urlencode(query_params),
            "",
        )
    )


def _filename_from_url(url: str) -> str | None:
    parsed_url = urlparse(url)
    spreadsheet_id = _google_spreadsheet_id(parsed_url.path)

    if parsed_url.netloc == "docs.google.com" and spreadsheet_id:
        return f"google-sheet-{spreadsheet_id}.xlsx"

    path = parsed_url.path

    if not path:
        return None

    filename = Path(path).name
    return filename or None


def _google_spreadsheet_id(path: str) -> str | None:
    path_parts = [part for part in path.split("/") if part]

    if len(path_parts) < 3:
        return None

    if path_parts[0] != "spreadsheets" or path_parts[1] != "d":
        return None

    return path_parts[2]


def _google_sheet_gid(query: str, fragment: str) -> str | None:
    query_gid = parse_qs(query).get("gid", [None])[0]

    if query_gid:
        return query_gid

    return parse_qs(fragment).get("gid", [None])[0]
