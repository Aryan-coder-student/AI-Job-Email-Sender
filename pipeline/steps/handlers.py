from __future__ import annotations

import subprocess
from pathlib import Path

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


class ParseResumeStep:
    step = PipelineStep.PARSE_RESUME

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        if context.resume_path is None:
            raise PipelineConfigurationError("resume_path is required for parse resume step.")

        try:
            context.parsed_resume = parse_resume_from_path(
                context.resume_path,
                config=ResumeParserConfig(),
                llm_router=build_default_llm_router(),
            )
        except Exception as error:
            raise PipelineStepError(f"Failed to parse resume: {error}") from error

        context.write_json(context.parsed_resume_path, context.parsed_resume.to_dict())


class ParseGitHubStep:
    step = PipelineStep.PARSE_GITHUB

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        if context.parsed_resume is None:
            raise PipelineConfigurationError("parsed_resume is required for parse GitHub step.")

        try:
            config = GitHubParserConfig(max_repos=options.max_repos)
            context.parsed_github = parse_github_from_resume(
                context.parsed_resume,
                config=config,
                llm_router=build_default_llm_router(),
            )
        except Exception as error:
            raise PipelineStepError(f"Failed to parse GitHub projects: {error}") from error

        context.write_json(context.github_projects_path, context.parsed_github.to_dict())


class BuildGraphStep:
    step = PipelineStep.BUILD_GRAPH

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        if context.parsed_resume is None or context.parsed_github is None:
            raise PipelineConfigurationError("parsed resume and github data are required.")
        if context.companies is None and context.companies_path is None:
            raise PipelineConfigurationError("companies data is required.")

        if context.companies is None and context.companies_path is not None:
            context.companies = load_json_file(str(context.companies_path))

        try:
            context.graph_result = run_build_knowledge_graph(
                parsed_resume_data=context.parsed_resume.to_dict(),
                parsed_github_data=context.parsed_github.to_dict(),
                company_records=context.companies,
                max_companies=options.max_companies,
                max_github_enrichment=options.max_github_enrichment,
                skip_enrichment=options.skip_enrichment,
                clear=options.clear_graph,
            )
        except Exception as error:
            raise PipelineStepError(f"Failed to build knowledge graph: {error}") from error

        context.candidate_id = context.graph_result["candidate"]["metadata"]["candidate_id"]
        context.write_json(context.graph_result_path, context.graph_result)


class RankProjectsStep:
    step = PipelineStep.RANK_PROJECTS

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        if context.candidate_id is None:
            raise PipelineConfigurationError("candidate_id is required for ranking.")
        if context.companies is None and context.companies_path is None:
            raise PipelineConfigurationError("companies data is required for ranking.")

        try:
            context.matches = run_rank_applications(
                company_records=context.companies,
                companies=context.companies_path if context.companies is None else None,
                company=options.target_company,
                candidate_id=context.candidate_id,
                job_url=options.job_url,
                top=options.top_matches,
            )
        except Exception as error:
            raise PipelineStepError(f"Failed to rank projects: {error}") from error

        context.write_json(context.matches_path, context.matches)


class GenerateDraftStep:
    step = PipelineStep.GENERATE_DRAFT

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        if context.parsed_resume is None:
            raise PipelineConfigurationError("parsed resume is required for draft generation.")
        if context.matches is None:
            raise PipelineConfigurationError("matches are required for draft generation.")
        if context.parsed_github is None:
            raise PipelineConfigurationError("parsed github data is required for draft generation.")
        if context.companies is None and context.companies_path is None:
            raise PipelineConfigurationError("companies data is required for draft generation.")

        recipient_email = resolve_recipient_email(
            company_name=options.target_company,
            companies=context.companies or [],
            parsed_resume=context.parsed_resume,
            explicit_email=options.recipient_email,
        )

        try:
            context.draft = run_generate_draft(
                parsed_resume_data=context.parsed_resume.to_dict(),
                company_name=options.target_company,
                matches=context.matches,
                company_records=context.companies,
                companies_path=context.companies_path,
                github_projects=[project.to_dict() for project in context.parsed_github.projects],
                recipient_email=recipient_email,
                enqueue=not options.no_enqueue,
            )
        except Exception as error:
            raise PipelineStepError(f"Failed to generate draft: {error}") from error

        context.write_json(context.draft_path, context.draft)


class ProcessMailQueueStep:
    step = PipelineStep.PROCESS_MAIL_QUEUE

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        try:
            context.mail_results = run_process_email_queue(
                limit=options.mail_limit,
                dry_run=options.dry_run,
            )
        except Exception as error:
            raise PipelineStepError(f"Failed to process mail queue: {error}") from error

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
