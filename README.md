# Job Send Crawl

Pipeline for parsing company spreadsheets, resumes, and GitHub profiles, building a knowledge graph, ranking project–company matches, and generating job application emails with LLM assistance.

## Setup

```bash
./setup_uv_env.sh
cp .env.example .env
```

The setup script installs `uv` if needed, creates `.venv`, and installs runtime plus test dependencies. Fill in API keys and service credentials in `.env` before running parsers or the pipeline.

## Infrastructure

Start Redis, Neo4j, and Qdrant:

```bash
docker compose up -d
./scripts/wait_for_services.sh
```

Neo4j Browser: http://localhost:7474  
Qdrant: http://localhost:6333

## Configuration

Settings load from environment variables and `.env` via Pydantic Settings (`app/core/settings.py`):

```python
from app.core.settings import get_settings

settings = get_settings()
```

See `.env.example` for all supported variables. Key groups:

| Group | Variables |
| --- | --- |
| LLM | `GROQ_API_KEY_1`–`4`, `GROQ_MODEL`, `OPENAI_*`, `GEMINI_*` |
| GitHub | `GITHUB_TOKEN` |
| Graph | `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` |
| Vector | `QDRANT_URL`, `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL` |
| Matching | `HYBRID_GRAPH_WEIGHT`, `HYBRID_VECTOR_WEIGHT`, `HYBRID_LLM_WEIGHT` |
| Mail / queue | `MAIL_PROVIDER`, `SMTP_*`, `REDIS_URL`, `EMAIL_QUEUE_KEY` |
| Celery | `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` |
| Logging | `LOG_LEVEL`, `LOG_FILE` |

Provider order for the LLM router is Groq keys 1–4, OpenAI, then Gemini. On rate limits, the router pauses that provider and tries the next.

## End-to-end pipeline

Place local inputs under `data/` (gitignored), for example:

- `data/AryanPahari.pdf`
- `data/companies_sheet.json`

Run the full pipeline:

```bash
./scripts/run_pipeline.sh --dry-run
```

Resume from a specific step:

```bash
./scripts/run_pipeline.sh --from-step 5 --dry-run
```

Useful flags:

| Flag | Description |
| --- | --- |
| `--from-step N` | Start at step 1–6 |
| `--company NAME` | Target company (default: `10up`) |
| `--recipient-email ADDR` | Draft recipient (default: first email from resume) |
| `--max-repos N` | GitHub repos to inspect (default: 100) |
| `--max-companies N` | Companies indexed in Neo4j (default: 25) |
| `--clear-graph` | Wipe Neo4j before graph build |
| `--skip-enrichment` | Skip LLM graph enrichment |
| `--skip-services` | Skip Neo4j/Qdrant wait |
| `--dry-run` | Mail step does not send (no SMTP required) |
| `--no-enqueue` | Write draft JSON only; skip Redis queue |

### Programmatic pipeline

The [`pipeline/`](pipeline/) package orchestrates the same flow in Python using the **Builder** and **Strategy** patterns:

```python
from pathlib import Path

from pipeline import ApplicationPipelineBuilder, PipelineOptions, PipelineStep

pipeline = (
    ApplicationPipelineBuilder(project_root=Path("."))
    .with_resume("data/AryanPahari.pdf")
    .with_companies("data/companies_sheet.json")
    .with_target_company("10up")
    .with_options(PipelineOptions(dry_run=True, from_step=1))
    .build()
)

result = pipeline.run()
print(result.context.draft)
```

Run a custom subset of steps:

```python
result = pipeline.run(
    steps=(
        PipelineStep.PARSE_RESUME,
        PipelineStep.PARSE_GITHUB,
        PipelineStep.BUILD_GRAPH,
    )
)
```

CLI entrypoint (also used by `scripts/run_pipeline.sh`):

```bash
.venv/bin/python -m pipeline.cli --from-step 5 --dry-run
.venv/bin/python -m pipeline.cli --steps parse_resume parse_github build_graph
```

### Pipeline steps

1. **Parse resume** → `data/parse_resume.json`
2. **Parse GitHub** → `data/github_projects_resume.json`
3. **Build graph + vectors** → `data/graph_build.json`
4. **Rank projects** → `data/matches.json`
5. **Generate draft** → `data/draft.json` (includes GitHub project links; deployed URL preferred over repo URL)
6. **Process mail queue** → `data/mail_queue_result.json`

## CLI reference

All CLIs use `cli/bootstrap.py` for `PYTHONPATH` setup. Run from the repo root with `.venv/bin/python -m ...`.

### Excel

```bash
.venv/bin/python -m cli.excel.parse_excel ./companies.xlsx --output-file data/companies_sheet.json
```

### Resume

```bash
.venv/bin/python -m cli.resume.parse_resume ./data/resume.pdf --output-file data/parse_resume.json
```

Use `--text-only` to extract text without LLM structured parsing.

### GitHub

```bash
.venv/bin/python -m cli.github.parse_github ./data/resume.pdf \
  --output-file data/github_projects_resume.json \
  --max-repos 50
```

Set `GITHUB_TOKEN` for reliable API access. Use `--readme-only` to skip LLM extraction.

### Knowledge graph

```bash
.venv/bin/python -m cli.graph.build_graph \
  --resume data/parse_resume.json \
  --github data/github_projects_resume.json \
  --companies data/companies_sheet.json \
  --clear \
  --output-file data/graph_build.json
```

`--clear` removes all Neo4j nodes before rebuild. By default only the first 25 company rows are indexed.

### Matching

```bash
.venv/bin/python -m cli.matching.rank_projects \
  --companies data/companies_sheet.json \
  --company 10up \
  --candidate-id candidate:your_github_username \
  --output-file data/matches.json
```

Read `candidate_id` from `data/graph_build.json` → `candidate.metadata.candidate_id`.

### Email draft

```bash
.venv/bin/python -m cli.emails.generate_draft \
  --resume data/parse_resume.json \
  --matches data/matches.json \
  --github data/github_projects_resume.json \
  --companies data/companies_sheet.json \
  --company 10up \
  --recipient-email you@example.com \
  --output-file data/draft.json
```

Drafts append a **GitHub project links** section (deployed link when available, otherwise repo link).

### Mail queue

```bash
.venv/bin/python -m cli.mail.process_queue --dry-run --output-file data/mail_queue_result.json
```

Requires `SMTP_USERNAME` and `SMTP_PASSWORD` only when sending (not in `--dry-run`).

### Direct SMTP test

```bash
.venv/bin/python -m cli.mail.send_mail --to hr@company.com --subject "Test" --body "Hello"
```

## Celery

```bash
.venv/bin/python -m celery -A app.celery.app worker --loglevel=info
```

Tasks live under `app/modules/*/tasks/` (graph, emails, matching, mail).

## Prompts

LLM prompt constants live in repo-root `prompts/`. Module `prompt_builder.py` files assemble runtime prompts from those constants.

## Tests

```bash
.venv/bin/python -m pytest
```

Module suites:

```bash
.venv/bin/python -m pytest tests/modules/excel
.venv/bin/python -m pytest tests/modules/llm
.venv/bin/python -m pytest tests/modules/resume
.venv/bin/python -m pytest tests/modules/github
.venv/bin/python -m pytest tests/modules/graph
.venv/bin/python -m pytest tests/modules/matching
.venv/bin/python -m pytest tests/modules/emails
.venv/bin/python -m pytest tests/core
.venv/bin/python -m pytest tests/celery
.venv/bin/python -m pytest tests/pipeline
```

## Project layout

```
pipeline/         ApplicationPipelineBuilder + step handlers
app/
  core/           settings, logging, exceptions, constants
  modules/        excel, resume, github, graph, vector, matching, emails, mail, llm
  celery/         Celery app and task registration
  redis/          email draft queue and rate limiting
cli/              thin CLI entrypoints
prompts/          shared LLM prompt constants
scripts/          run_pipeline.sh, wait_for_services.sh
tests/
```

Graph architecture details: `app/modules/graph/doc/ARCHITECTURE.md`
