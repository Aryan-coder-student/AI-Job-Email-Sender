from __future__ import annotations

from app.modules.emails.tasks.runner import run_generate_draft
from app.modules.github.config import GitHubParserConfig
from app.modules.github.parser import parse_github_from_resume
from app.modules.graph.tasks.runner import run_build_knowledge_graph
from app.modules.llm.factory import build_default_llm_router
from app.modules.mail.tasks.runner import run_process_email_queue
from app.modules.matching.tasks.runner import run_rank_applications
from app.modules.resume.config import ResumeParserConfig
from app.modules.resume.parser import parse_resume_from_path
from pipeline.config import PipelineOptions
from pipeline.context import PipelineContext
from pipeline.steps.base import BaseStepHandler
from pipeline.types import PipelineStep
from pipeline.utils import resolve_recipient_email
from pipeline.validation import (
    require_value,
    validate_companies_loaded,
    validate_resume_path,
)


class ParseResumeStep(BaseStepHandler):
    step = PipelineStep.PARSE_RESUME

    def validate(self, context: PipelineContext, options: PipelineOptions) -> None:
        validate_resume_path(context)

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        resume_path = require_value(
            context.resume_path,
            "resume_path is required for parse resume step.",
        )
        context.parsed_resume = parse_resume_from_path(
            resume_path,
            config=ResumeParserConfig(),
            llm_router=build_default_llm_router(),
        )
        context.write_json(context.parsed_resume_path, context.parsed_resume.to_dict())


class ParseGitHubStep(BaseStepHandler):
    step = PipelineStep.PARSE_GITHUB

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        parsed_resume = require_value(
            context.parsed_resume,
            "parsed_resume is required for parse GitHub step.",
        )
        config = GitHubParserConfig(max_repos=options.max_repos)
        context.parsed_github = parse_github_from_resume(
            parsed_resume,
            config=config,
            llm_router=build_default_llm_router(),
        )
        context.write_json(context.github_projects_path, context.parsed_github.to_dict())


class BuildGraphStep(BaseStepHandler):
    step = PipelineStep.BUILD_GRAPH
    requires_services = True

    def validate(self, context: PipelineContext, options: PipelineOptions) -> None:
        validate_companies_loaded(context)

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        parsed_resume = require_value(context.parsed_resume, "parsed resume data is required.")
        parsed_github = require_value(context.parsed_github, "parsed github data is required.")
        companies = require_value(context.companies, "companies data is required.")
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


class RankProjectsStep(BaseStepHandler):
    step = PipelineStep.RANK_PROJECTS
    requires_services = True

    def validate(self, context: PipelineContext, options: PipelineOptions) -> None:
        validate_companies_loaded(context)

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        candidate_id = require_value(context.candidate_id, "candidate_id is required for ranking.")
        companies = require_value(context.companies, "companies data is required for ranking.")
        context.matches = {}
        for comp in companies:
            comp_name = comp.get("company_name", "Unknown")
            context.matches[comp_name] = run_rank_applications(
                company_records=companies,
                companies=None,
                company=comp_name,
                candidate_id=candidate_id,
                job_url=options.job_url,
                top=options.top_matches,
            )
        context.write_json(context.matches_path, context.matches)


class GenerateDraftStep(BaseStepHandler):
    step = PipelineStep.GENERATE_DRAFT

    def validate(self, context: PipelineContext, options: PipelineOptions) -> None:
        validate_companies_loaded(context)

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        parsed_resume = require_value(
            context.parsed_resume,
            "parsed resume is required for draft generation.",
        )
        parsed_github = require_value(
            context.parsed_github,
            "parsed github data is required for draft generation.",
        )
        matches = require_value(context.matches, "matches are required for draft generation.")
        companies = require_value(
            context.companies,
            "companies data is required for draft generation.",
        )
        context.drafts = {}
        for comp in companies:
            comp_name = comp.get("company_name", "Unknown")
            comp_matches = matches.get(comp_name, [])
            
            recipient_email = resolve_recipient_email(
                company_name=comp_name,
                companies=companies,
                parsed_resume=parsed_resume,
                explicit_email=options.recipient_email,
            )

            context.drafts[comp_name] = run_generate_draft(
                parsed_resume_data=parsed_resume.to_dict(),
                company_name=comp_name,
                matches=comp_matches,
                company_records=companies,
                companies_path=context.companies_path,
                github_projects=[project.to_dict() for project in parsed_github.projects],
                recipient_email=recipient_email,
                enqueue=not options.no_enqueue,
            )
        context.write_json(context.drafts_path, context.drafts)


class ProcessMailQueueStep(BaseStepHandler):
    step = PipelineStep.PROCESS_MAIL_QUEUE

    def execute(self, context: PipelineContext, options: PipelineOptions) -> None:
        context.mail_results = run_process_email_queue(
            limit=options.mail_limit,
            dry_run=options.dry_run,
        )
        context.write_json(context.mail_result_path, context.mail_results)
