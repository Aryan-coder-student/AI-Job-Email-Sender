from __future__ import annotations

from unittest.mock import patch

import pytest

from app.modules.emails.tasks import cli as emails_cli
from app.modules.graph.tasks import cli as graph_cli
from app.modules.mail.tasks import cli as mail_cli
from app.modules.matching.tasks import cli as matching_cli


def test_graph_build_parser_requires_input_paths() -> None:
    with pytest.raises(SystemExit):
        graph_cli.build_parser().parse_args([])


def test_graph_main_calls_runner() -> None:
    argv = [
        "--resume",
        "resume.json",
        "--github",
        "github.json",
        "--companies",
        "companies.json",
    ]
    with patch("app.modules.graph.tasks.cli.run_build_knowledge_graph") as run_mock:
        run_mock.return_value = {"candidate": {}}
        assert graph_cli.main(argv) == 0
        run_mock.assert_called_once()


def test_emails_build_parser_requires_company() -> None:
    with pytest.raises(SystemExit):
        emails_cli.build_parser().parse_args(["--resume", "resume.json"])


def test_emails_main_requires_matches() -> None:
    argv = ["--resume", "resume.json", "--company", "Acme"]
    with pytest.raises(SystemExit, match="--matches is required"):
        emails_cli.main(argv)


def test_emails_main_calls_runner() -> None:
    argv = [
        "--resume",
        "resume.json",
        "--company",
        "Acme",
        "--matches",
        "matches.json",
    ]
    with patch("app.modules.emails.tasks.cli.run_generate_draft") as run_mock:
        run_mock.return_value = {"draft_id": "draft-1"}
        assert emails_cli.main(argv) == 0
        run_mock.assert_called_once()


def test_mail_main_calls_runner() -> None:
    with patch("app.modules.mail.tasks.cli.run_process_email_queue") as run_mock:
        run_mock.return_value = [{"status": "dry_run"}]
        assert mail_cli.main(["--dry-run"]) == 0
        run_mock.assert_called_once_with(limit=10, dry_run=True)


def test_matching_main_calls_runner() -> None:
    argv = [
        "--companies",
        "companies.json",
        "--company",
        "Acme",
        "--candidate-id",
        "candidate:test",
    ]
    with patch("app.modules.matching.tasks.cli.run_rank_applications") as run_mock:
        run_mock.return_value = [{"project_name": "demo"}]
        assert matching_cli.main(argv) == 0
        run_mock.assert_called_once()


def test_mail_parser_defaults() -> None:
    args = mail_cli.build_parser().parse_args([])
    assert args.limit == 10
    assert args.dry_run is False
    assert args.output_file is None


def test_matching_parser_defaults() -> None:
    args = matching_cli.build_parser().parse_args(
        ["--companies", "companies.json", "--company", "Acme", "--candidate-id", "id"]
    )
    assert args.top == 5
    assert args.job_url is None
    assert args.output_file is None
