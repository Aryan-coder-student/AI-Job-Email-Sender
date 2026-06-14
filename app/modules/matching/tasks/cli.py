from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.modules.matching.tasks.runner import run_rank_applications


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rank projects for one company/job row.")
    parser.add_argument("--companies", type=Path, required=True)
    parser.add_argument("--company", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--job-url", default=None)
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--output-file", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    payload = run_rank_applications(
        companies=args.companies,
        company=args.company,
        candidate_id=args.candidate_id,
        job_url=args.job_url,
        top=args.top,
    )
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output_file:
        args.output_file.write_text(f"{text}\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
