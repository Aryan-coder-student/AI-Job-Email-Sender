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
from app.modules.github.config import GitHubParserConfig  # noqa: E402
from app.modules.github.parser import parse_github_from_resume  # noqa: E402
from app.modules.llm.factory import build_default_llm_router  # noqa: E402
from app.modules.resume.config import ResumeParserConfig  # noqa: E402
from app.modules.resume.parser import parse_resume_from_path  # noqa: E402
from setting import RESUME_ALLOWED_EXTENSIONS  # noqa: E402


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Parse a resume file, extract the GitHub profile URL, "
            "and return structured project data from READMEs."
        ),
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Local resume file path (PDF, DOCX, TXT).",
    )
    parser.add_argument(
        "--readme-only",
        action="store_true",
        help="Fetch READMEs only, do not use LLM for structured extraction.",
    )
    parser.add_argument(
        "--max-repos",
        type=positive_int,
        default=100,
        help="Maximum number of repositories to inspect. Defaults to 100.",
    )
    parser.add_argument(
        "--min-readme-chars",
        type=positive_int,
        default=80,
        help="Minimum README length required to include a repository. Defaults to 80.",
    )
    parser.add_argument(
        "--max-readme-chars",
        type=positive_int,
        default=20000,
        help="Maximum README characters passed to the LLM. Defaults to 20000.",
    )
    parser.add_argument(
        "--llm-max-tokens",
        type=positive_int,
        default=1500,
        help="Maximum output tokens for each repository LLM call. Defaults to 1500.",
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
        help="Optional path to write JSON output instead of printing to stdout.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON instead of pretty JSON.",
    )
    return parser


def build_github_config(args: argparse.Namespace) -> GitHubParserConfig:
    return GitHubParserConfig(
        max_repos=args.max_repos,
        min_readme_chars=args.min_readme_chars,
        max_readme_chars=args.max_readme_chars,
        llm_max_tokens=args.llm_max_tokens,
        llm_max_workers=args.llm_max_workers,
    )


def build_resume_config() -> ResumeParserConfig:
    return ResumeParserConfig(allowed_extensions=RESUME_ALLOWED_EXTENSIONS)


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


def main(argv: Sequence[str] | None = None) -> int:
    dotenv.load_dotenv()

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        resume_config = build_resume_config()
        resume_config.validate()

        github_config = build_github_config(args)
        github_config.validate()

        resume_router = None
        github_router = None

        if not args.readme_only:
            try:
                resume_router = build_default_llm_router()
                github_router = resume_router
            except Exception as error:
                print(f"Failed to initialize LLM router: {error}", file=sys.stderr)
                return 1

        parsed_resume = parse_resume_from_path(
            path=args.source,
            config=resume_config,
            llm_router=resume_router,
        )

        if not parsed_resume.links.github:
            print("Error: Resume does not contain a GitHub profile URL.", file=sys.stderr)
            return 1

        parsed_github = parse_github_from_resume(
            parsed_resume,
            config=github_config,
            llm_router=github_router,
        )

        write_json_output(parsed_github.to_dict(), args.output_file, args.compact)
    except (AppError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Unexpected Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
