#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence
import dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.exceptions import AppError  # noqa: E402
from app.modules.llm.factory import build_default_llm_router  # noqa: E402
from app.modules.resume.config import ResumeParserConfig  # noqa: E402
from app.modules.resume.parser import parse_resume_from_path  # noqa: E402
from setting import RESUME_ALLOWED_EXTENSIONS  # noqa: E402


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse a local resume file and print the extracted JSON structure.",
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Local resume file path (PDF, DOCX, TXT).",
    )
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Only extract text, do not use LLM for structured extraction.",
    )
    parser.add_argument(
        "--max-file-size-mb",
        type=positive_float,
        default=5.0,
        help="Maximum allowed file size in MB. Defaults to 5.",
    )
    parser.add_argument(
        "--max-cleaned-text-chars",
        type=positive_int,
        default=200000,
        help="Maximum characters of cleaned text to pass to the LLM. Defaults to 200000.",
    )
    parser.add_argument(
        "--llm-max-tokens",
        type=positive_int,
        default=1800,
        help="Maximum output tokens for the LLM. Defaults to 1800.",
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


def build_config(args: argparse.Namespace) -> ResumeParserConfig:
    return ResumeParserConfig(
        allowed_extensions=RESUME_ALLOWED_EXTENSIONS,
        max_file_size_bytes=int(args.max_file_size_mb * 1024 * 1024),
        max_cleaned_text_chars=args.max_cleaned_text_chars,
        llm_max_tokens=args.llm_max_tokens,
    )


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


def main(argv: Sequence[str] | None = None) -> int:
    dotenv.load_dotenv()

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        config = build_config(args)
        config.validate()

        router = None
        if not args.text_only:
            try:
                router = build_default_llm_router()
            except Exception as e:
                print(f"Failed to initialize LLM router: {e}", file=sys.stderr)
                return 1

        parsed_resume = parse_resume_from_path(
            path=args.source,
            config=config,
            llm_router=router,
        )

        write_json_output(parsed_resume.to_dict(), args.output_file, args.compact)
    except (AppError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
