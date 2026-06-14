from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.modules.graph.tasks.runner import run_build_knowledge_graph


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build knowledge graph and vector indexes.")
    parser.add_argument("--resume", type=Path, required=True)
    parser.add_argument("--github", type=Path, required=True)
    parser.add_argument("--companies", type=Path, required=True)
    parser.add_argument("--candidate-id", default=None)
    parser.add_argument("--max-companies", type=int, default=25)
    parser.add_argument("--max-github-enrichment", type=int, default=10)
    parser.add_argument("--skip-enrichment", action="store_true")
    parser.add_argument("--clear", action="store_true")
    parser.add_argument("--output-file", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    payload = run_build_knowledge_graph(
        resume=args.resume,
        github=args.github,
        companies=args.companies,
        candidate_id=args.candidate_id,
        max_companies=args.max_companies,
        max_github_enrichment=args.max_github_enrichment,
        skip_enrichment=args.skip_enrichment,
        clear=args.clear,
    )
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output_file:
        args.output_file.write_text(f"{text}\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
