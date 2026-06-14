from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.modules.emails.tasks.runner import run_generate_draft


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate job application email drafts.")
    parser.add_argument("--resume", type=Path, required=True)
    parser.add_argument("--matches", type=Path, default=None, help="Ranked project matches JSON.")
    parser.add_argument("--companies", type=Path, default=None, help="Parsed company records JSON.")
    parser.add_argument("--github", type=Path, default=None, help="Parsed GitHub projects JSON.")
    parser.add_argument("--company", required=True)
    parser.add_argument("--recipient-email", default=None)
    parser.add_argument("--no-enqueue", action="store_true")
    parser.add_argument("--output-file", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.matches is None:
        raise SystemExit("--matches is required.")

    payload = run_generate_draft(
        resume=args.resume,
        company_name=args.company,
        matches_path=args.matches,
        companies_path=args.companies,
        github_path=args.github,
        recipient_email=args.recipient_email,
        enqueue=not args.no_enqueue,
    )
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output_file:
        args.output_file.write_text(f"{text}\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
