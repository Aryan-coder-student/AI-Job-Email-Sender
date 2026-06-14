#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.exceptions import AppError  # noqa: E402
from app.modules.github.config import GitHubParserConfig  # noqa: E402
from app.modules.github.parser import parse_github_profile  # noqa: E402
from app.modules.llm.factory import build_default_llm_router  # noqa: E402


def positive_int(value: str) -> int:
    try:
        parsed_value = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error

    if parsed_value < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")

    return parsed_value


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse a GitHub profile URL and extract structured project data from READMEs.",
    )
    parser.add_argument(
        "github_url",
        help="GitHub profile or repository URL.",
    )
    parser.add_argument(
        "--readme-only",
        action="store_true",
        help="Fetch READMEs only, skip LLM structured extraction.",
    )
    parser.add_argument(
        "--llm-max-workers",
        type=positive_int,
        default=5,
        help="Maximum parallel LLM requests for README extraction. Defaults to 5.",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Optional path to write JSON output.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON instead of pretty JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    dotenv.load_dotenv()
    args = build_arg_parser().parse_args(argv)

    try:
        llm_router = None
        if not args.readme_only:
            llm_router = build_default_llm_router()

        config = GitHubParserConfig(llm_max_workers=args.llm_max_workers)
        profile = parse_github_profile(
            args.github_url,
            config=config,
            llm_router=llm_router,
        )
        payload = profile.to_dict()
        indent = None if args.compact else 2
        json_text = json.dumps(payload, indent=indent, default=str, ensure_ascii=False)

        if args.output_file:
            args.output_file.write_text(f"{json_text}\n", encoding="utf-8")
        else:
            print(json_text)
    except AppError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Unexpected Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
