from __future__ import annotations

import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, TypeVar

from app.modules.emails.tasks.runner import run_generate_draft
from app.modules.github.config import GitHubParserConfig
from app.modules.github.parser import parse_github_from_resume
from app.modules.graph.serializers import load_json_file
from app.modules.graph.tasks.runner import run_build_knowledge_graph
from app.modules.llm.factory import build_default_llm_router
from app.modules.mail.tasks.runner import run_process_email_queue
from app.modules.matching.tasks.runner import run_rank_applications
from app.modules.resume.config import ResumeParserConfig
from app.modules.resume.parser import parse_resume_from_path
from pipeline.config import PipelineOptions
from pipeline.context import PipelineContext
from pipeline.exceptions import PipelineConfigurationError, PipelineStepError
from pipeline.types import PipelineStep
from pipeline.utils import resolve_recipient_email

T = TypeVar("T")


class ParseResumeStep:
    step = PipelineStep.PARSE_RESUME

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        resume_path = _required(
            context.resume_path,
            "resume_path is required for parse resume step.",
        )
        with _step_failure("Failed to parse resume"):
            context.parsed_resume = parse_resume_from_path(
                resume_path,
                config=ResumeParserConfig(),
                llm_router=build_default_llm_router(),
            )

        context.write_json(context.parsed_resume_path, context.parsed_resume.to_dict())


class ParseGitHubStep:
    step = PipelineStep.PARSE_GITHUB

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        parsed_resume = _required(
            context.parsed_resume,
            "parsed_resume is required for parse GitHub step.",
        )
        with _step_failure("Failed to parse GitHub projects"):
            config = GitHubParserConfig(max_repos=options.max_repos)
            context.parsed_github = parse_github_from_resume(
                parsed_resume,
                config=config,
                llm_router=build_default_llm_router(),
            )

        context.write_json(context.github_projects_path, context.parsed_github.to_dict())


class BuildGraphStep:
    step = PipelineStep.BUILD_GRAPH

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        parsed_resume = _required(context.parsed_resume, "parsed resume data is required.")
        parsed_github = _required(context.parsed_github, "parsed github data is required.")
        companies = _company_records(context, "companies data is required.")
        with _step_failure("Failed to build knowledge graph"):
            context.graph_result = run_build_knowledge_graph(
                parsed_resume_data=parsed_resume.to_dict(),
                parsed_github_data=parsed_github.to_dict(),
                company_records=companies,
                max_companies=options.max_companies,
                max_github_enrichment=options.max_github_enrichment,
                skip_enrichment=options.skip_enrichment,
                clear=options.clear_graph,
            )

        context.candidate_id = context.graph_result["candidate"]["metadata"]["candidate_id"]
        context.write_json(context.graph_result_path, context.graph_result)


class RankProjectsStep:
    step = PipelineStep.RANK_PROJECTS

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        candidate_id = _required(context.candidate_id, "candidate_id is required for ranking.")
        _require_company_source(context, "companies data is required for ranking.")
        with _step_failure("Failed to rank projects"):
            context.matches = run_rank_applications(
                company_records=context.companies,
                companies=context.companies_path if context.companies is None else None,
                company=options.target_company,
                candidate_id=candidate_id,
                job_url=options.job_url,
                top=options.top_matches,
            )

        context.write_json(context.matches_path, context.matches)


class GenerateDraftStep:
    step = PipelineStep.GENERATE_DRAFT

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        parsed_resume = _required(
            context.parsed_resume,
            "parsed resume is required for draft generation.",
        )
        parsed_github = _required(
            context.parsed_github,
            "parsed github data is required for draft generation.",
        )
        matches = _required(context.matches, "matches are required for draft generation.")
        companies = _company_records(
            context,
            "companies data is required for draft generation.",
        )
        recipient_email = resolve_recipient_email(
            company_name=options.target_company,
            companies=companies,
            parsed_resume=parsed_resume,
            explicit_email=options.recipient_email,
        )

        with _step_failure("Failed to generate draft"):
            context.draft = run_generate_draft(
                parsed_resume_data=parsed_resume.to_dict(),
                company_name=options.target_company,
                matches=matches,
                company_records=companies,
                companies_path=context.companies_path,
                github_projects=[project.to_dict() for project in parsed_github.projects],
                recipient_email=recipient_email,
                enqueue=not options.no_enqueue,
            )

        context.write_json(context.draft_path, context.draft)


class ProcessMailQueueStep:
    step = PipelineStep.PROCESS_MAIL_QUEUE

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        with _step_failure("Failed to process mail queue"):
            context.mail_results = run_process_email_queue(
                limit=options.mail_limit,
                dry_run=options.dry_run,
            )

        context.write_json(context.mail_result_path, context.mail_results)


def ensure_services_ready(*, project_root: Path) -> None:
    script_path = project_root / "scripts" / "wait_for_services.sh"
    if not script_path.is_file():
        raise PipelineConfigurationError(f"Missing service check script: {script_path}")

    result = subprocess.run(
        [str(script_path)],
        cwd=project_root,
        check=False,
    )
    if result.returncode != 0:
        raise PipelineStepError("Infrastructure services are not ready.")


def _required(value: T | None, message: str) -> T:
    if value is None:
        raise PipelineConfigurationError(message)
    return value


def _require_company_source(context: PipelineContext, message: str) -> None:
    if context.companies is not None or context.companies_path is not None:
        return
    raise PipelineConfigurationError(message)


def _company_records(context: PipelineContext, message: str) -> list[dict[str, Any]]:
    if context.companies is not None:
        return context.companies

    companies_path = _required(context.companies_path, message)
    context.companies = load_json_file(str(companies_path))
    return context.companies


@contextmanager
def _step_failure(message: str) -> Iterator[None]:
    try:
        yield
    except Exception as error:
        raise PipelineStepError(f"{message}: {error}") from error
