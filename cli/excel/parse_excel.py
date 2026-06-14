#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlparse

from cli.bootstrap import bootstrap_cli
from app.core.exceptions import AppError
from app.modules.excel.config import ExcelParserConfig
from app.modules.excel.parser import ParsedExcelWorkbook
from app.modules.excel.sources import parse_excel_from_path, parse_excel_from_url


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse a local or remote Excel file and print the normalized result.",
    )
    parser.add_argument(
        "source",
        help="Local Excel file path or HTTP/HTTPS Excel URL.",
    )
    parser.add_argument(
        "--source-type",
        choices=("auto", "path", "url"),
        default="auto",
        help="How to interpret source. Defaults to auto.",
    )
    parser.add_argument(
        "--sheet-count",
        type=positive_int,
        default=1,
        help="Number of sheets to parse. Defaults to 1.",
    )
    parser.add_argument(
        "--all-sheets",
        action="store_true",
        help="Parse all sheets. Overrides --sheet-count.",
    )
    parser.add_argument(
        "--sheet-name",
        action="append",
        default=[],
        help="Specific sheet name to parse. Can be passed multiple times.",
    )
    parser.add_argument(
        "--max-rows",
        type=positive_int,
        default=None,
        help="Maximum populated rows to parse per sheet. Defaults to all populated rows.",
    )
    parser.add_argument(
        "--max-empty-ratio",
        type=ratio,
        default=0.9,
        help=(
            "Skip rows with this empty-cell ratio or higher. "
            "Defaults to 0.9. Use 0.75 for noisier sheets."
        ),
    )
    parser.add_argument(
        "--keep-sparse-rows",
        action="store_true",
        help="Disable empty-cell ratio filtering.",
    )
    parser.add_argument(
        "--header-row",
        type=positive_int,
        default=1,
        help="1-based row number containing headers. Defaults to 1.",
    )
    parser.add_argument(
        "--download-timeout",
        type=positive_int,
        default=20,
        help="Download timeout in seconds for URL sources. Defaults to 20.",
    )
    parser.add_argument(
        "--max-download-mb",
        type=positive_float,
        default=10.0,
        help="Maximum URL download size in MB. Defaults to 10.",
    )
    parser.add_argument(
        "--output",
        choices=("records", "workbook"),
        default="records",
        help="Print normalized company records or the full workbook structure.",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Optional path to write JSON output instead of printing to stdout.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON instead of pretty JSON.",
    )
    return parser


def build_config(args: argparse.Namespace) -> ExcelParserConfig:
    sheet_count = None if args.all_sheets else args.sheet_count
    max_empty_ratio = None if args.keep_sparse_rows else args.max_empty_ratio

    return ExcelParserConfig(
        sheet_count=sheet_count,
        max_rows=args.max_rows,
        max_empty_ratio=max_empty_ratio,
        header_row=args.header_row,
        sheet_names=tuple(args.sheet_name),
        download_timeout_seconds=args.download_timeout,
        max_download_bytes=int(args.max_download_mb * 1024 * 1024),
    )


def parse_source(
    source: str,
    source_type: str,
    config: ExcelParserConfig,
) -> ParsedExcelWorkbook:
    resolved_source_type = resolve_source_type(source, source_type)

    if resolved_source_type == "url":
        return parse_excel_from_url(source, config=config)

    return parse_excel_from_path(source, config=config)


def resolve_source_type(source: str, source_type: str) -> str:
    if source_type != "auto":
        return source_type

    parsed_source = urlparse(source)

    if parsed_source.scheme in {"http", "https"}:
        return "url"

    return "path"


def workbook_to_payload(workbook: ParsedExcelWorkbook, output: str) -> Any:
    if output == "workbook":
        return workbook.to_dict()

    return workbook.to_company_records()


def write_json_output(
    payload: Any,
    output_file: Path | None,
    compact: bool,
) -> None:
    indent = None if compact else 2
    json_text = json.dumps(payload, indent=indent, default=str, ensure_ascii=False)

    if output_file:
        output_file.write_text(f"{json_text}\n", encoding="utf-8")
        return

    print(json_text)


def positive_int(value: str) -> int:
    try:
        parsed_value = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error

    if parsed_value < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")

    return parsed_value


def positive_float(value: str) -> float:
    try:
        parsed_value = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive number") from error

    if parsed_value <= 0:
        raise argparse.ArgumentTypeError("must be a positive number")

    return parsed_value


def ratio(value: str) -> float:
    parsed_value = positive_float(value)

    if parsed_value > 1:
        raise argparse.ArgumentTypeError("must be between 0 and 1")

    return parsed_value


def main(argv: Sequence[str] | None = None) -> int:
    bootstrap_cli()
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        config = build_config(args)
        config.validate()
        workbook = parse_source(args.source, args.source_type, config)
        payload = workbook_to_payload(workbook, args.output)
        write_json_output(payload, args.output_file, args.compact)
    except (AppError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
