from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.modules.mail.tasks.runner import run_process_email_queue


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send queued application emails.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-file", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    payload = run_process_email_queue(limit=args.limit, dry_run=args.dry_run)
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output_file:
        args.output_file.write_text(f"{text}\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
