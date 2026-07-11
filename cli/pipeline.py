#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cli.bootstrap import bootstrap_cli
from pipeline.builder import ApplicationPipelineBuilder
from pipeline.config import PipelineOptions
from pipeline.exceptions import PipelineError
from pipeline.types import PipelineStep


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the job application pipeline using ApplicationPipelineBuilder.",
    )
    parser.add_argument("--resume", type=Path, default=None, help="Resume PDF/DOCX/TXT path.")
    parser.add_argument(
        "--companies",
        type=Path,
        default=None,
        help="Parsed companies JSON path.",
    )
    parser.add_argument("--company", default="10up", help="Target company name.")
    parser.add_argument("--recipient-email", default=None, help="Draft recipient email.")
    parser.add_argument("--output-dir", type=Path, default=Path("data"), help="Artifact output directory.")
    parser.add_argument("--from-step", type=int, default=1, help="Start at pipeline step 1-6.")
    parser.add_argument("--max-repos", type=int, default=100)
    parser.add_argument("--max-companies", type=int, default=25)
    parser.add_argument("--skip-services", action="store_true")
    parser.add_argument("--skip-enrichment", action="store_true")
    parser.add_argument("--clear-graph", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-enqueue", action="store_true")
    parser.add_argument(
        "--steps",
        nargs="+",
        choices=[step.name.lower() for step in PipelineStep],
        default=None,
        help="Custom step list, e.g. parse_resume build_graph rank_projects",
    )
    return parser


def _parse_steps(raw_steps: list[str] | None) -> tuple[PipelineStep, ...] | None:
    if raw_steps is None:
        return None
    mapping = {step.name.lower(): step for step in PipelineStep}
    return tuple(mapping[name.lower()] for name in raw_steps)


def main(argv: list[str] | None = None) -> int:
    bootstrap_cli()

    args = build_parser().parse_args(argv)
    project_root = Path.cwd()

    resume_path = args.resume or project_root / "data" / "AryanPahari.pdf"
    companies_path = args.companies or project_root / "data" / "companies_sheet.json"

    options = PipelineOptions(
        target_company=args.company,
        recipient_email=args.recipient_email,
        from_step=args.from_step,
        dry_run=args.dry_run,
        no_enqueue=args.no_enqueue,
        skip_enrichment=args.skip_enrichment,
        skip_services=args.skip_services,
        clear_graph=args.clear_graph,
        max_repos=args.max_repos,
        max_companies=args.max_companies,
        output_dir=args.output_dir,
        steps=_parse_steps(args.steps),
    )

    builder = (
        ApplicationPipelineBuilder(project_root=project_root)
        .with_companies(companies_path)
        .with_target_company(args.company)
        .with_recipient_email(args.recipient_email)
        .with_output_dir(args.output_dir)
        .with_options(options)
    )

    if args.from_step <= 2:
        builder = builder.with_resume(resume_path)

    try:
        result = builder.build().run()
    except PipelineError as error:
        print(f"Pipeline failed: {error}", file=sys.stderr)
        return 1

    context = result.context
    print("Pipeline finished.")
    print(f"  steps executed: {result.steps_executed}")
    print(f"  resume parsed:  {context.parsed_resume_path}")
    print(f"  github parsed:  {context.github_projects_path}")
    print(f"  graph result:   {context.graph_result_path}")
    print(f"  matches:        {context.matches_path}")
    print(f"  draft:          {context.draft_path}")
    print(f"  mail result:    {context.mail_result_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
