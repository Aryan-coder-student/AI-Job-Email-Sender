# Job Send Crawl

Pipeline for parsing company spreadsheets, resumes, and GitHub profiles, then generating and sending job application emails with LLM assistance.

## Setup

Run the project setup script:

```bash
./setup_uv_env.sh
```

The script installs `uv` if needed, creates `.venv`, and installs runtime plus test dependencies.

Copy environment variables into a local `.env` file before running parsers or CLIs that call external APIs.

## Environment Variables

```bash
# Groq (primary LLM provider; at least one key required for structured extraction)
GROQ_API_KEY_1=
GROQ_API_KEY_2=
GROQ_API_KEY_3=
GROQ_API_KEY_4=
GROQ_MODEL=
OPENAI_API_KEY=
OPENAI_MODEL=
GEMINI_API_KEY=
GEMINI_MODEL=

# GitHub API token for README fetching
GITHUB_TOKEN=

# Logging
LOG_LEVEL=INFO
# LOG_FILE=logs/app.log
```

Provider order for the LLM router is Groq keys 1–4, OpenAI, then Gemini. If a provider returns a rate-limit response, the router pauses it temporarily and tries the next provider.

## Tests

Run all tests:

```bash
.venv/bin/python -m pytest
```

Run module-specific suites:

```bash
.venv/bin/python -m pytest tests/modules/excel
.venv/bin/python -m pytest tests/modules/llm
.venv/bin/python -m pytest tests/modules/resume
.venv/bin/python -m pytest tests/modules/github
.venv/bin/python -m pytest tests/core
```

## Excel Parser CLI

Parse a local Excel file and print normalized company records:

```bash
.venv/bin/python -m cli.excel.parse_excel ./companies.xlsx
```

Parse an Excel URL:

```bash
.venv/bin/python -m cli.excel.parse_excel "https://example.com/companies.xlsx"
```

Parse a public Google Sheet link:

```bash
.venv/bin/python -m cli.excel.parse_excel \
  "https://docs.google.com/spreadsheets/d/1TLJSlNxCbwRNxy14Toe1PYwbCTY7h0CNHeer9J0VRzE/htmlview#gid=1279011369"
```

Useful options:

```bash
.venv/bin/python -m cli.excel.parse_excel ./companies.xlsx \
  --sheet-name Companies \
  --max-rows 5 \
  --max-empty-ratio 0.75 \
  --output workbook
```

By default, the parser skips rows where 90% or more cells are empty. For noisy sheets, lower the threshold, for example `--max-empty-ratio 0.75`. To keep sparse rows, use `--keep-sparse-rows`.

## LLM Router

Basic usage:

```python
from app.modules.llm.factory import build_default_llm_router
from app.modules.llm.interface import LLMMessage, LLMRequest

router = build_default_llm_router()
response = router.generate(
    LLMRequest(
        messages=[
            LLMMessage(role="system", content="Write concise job application emails."),
            LLMMessage(role="user", content="Draft an email for Acme."),
        ]
    )
)

print(response.provider, response.content)
```

## Resume Parser

Supported resume file types:

```txt
.txt
.pdf
.docx
```

Dependencies:

```txt
langchain
pypdf
python-docx
```

Basic usage:

```python
from app.modules.llm.factory import build_default_llm_router
from app.modules.resume.parser import parse_resume_from_path

router = build_default_llm_router()
resume = parse_resume_from_path("./resume.pdf", llm_router=router)
print(resume.candidate_name)
print(resume.skills)
print(resume.links.github)
```

The parser extracts and cleans resume text locally (including embedded PDF hyperlinks), prepares a strict Pydantic schema using LangChain's `PydanticOutputParser` for structured output, then asks the configured LLM router to return structured JSON. Structured fields include candidate name, summary, skills, experience, projects, achievements, research work, education, emails, phones, GitHub, LinkedIn, portfolio, and URLs.

If you call the parser without `llm_router`, it still validates the file and returns the cleaned raw text, but structured fields stay empty. This is useful for testing upload and text extraction without spending LLM tokens.

## Resume Parser CLI

Parse a local resume file and print the extracted JSON structure:

```bash
.venv/bin/python -m cli.resume.parse_resume ./resume.pdf
```

Useful options:

```bash
.venv/bin/python -m cli.resume.parse_resume ./resume.pdf \
  --output-file parsed.json \
  --text-only
```

Use `--text-only` to skip LLM processing and only extract raw text and metadata.

## GitHub Parser

Fetches public repositories for a GitHub profile, reads non-empty READMEs, and uses the LLM to infer structured project data:

- `tech_stack.backend`, `tech_stack.frontend`, `tech_stack.ai_ml`
- `summary`
- `non_tech_tags`
- `deployed_link`
- `repo_link` (from the GitHub API, not the LLM)

Set `GITHUB_TOKEN` in `.env` for reliable API access and higher rate limits.

Basic usage:

```python
from app.modules.github.parser import parse_github_profile
from app.modules.llm.factory import build_default_llm_router

router = build_default_llm_router()
profile = parse_github_profile(
    "https://github.com/your-username",
    llm_router=router,
)
print(profile.github_username, len(profile.projects))
```

Parse from an already-extracted resume:

```python
from app.modules.github.parser import parse_github_from_resume
from app.modules.llm.factory import build_default_llm_router
from app.modules.resume.parser import parse_resume_from_path

router = build_default_llm_router()
resume = parse_resume_from_path("./resume.pdf", llm_router=router)
profile = parse_github_from_resume(resume, llm_router=router)
```

Pass `llm_router=None` or use `--readme-only` in the CLI to fetch READMEs without LLM extraction.

## GitHub Parser CLI

Parse a resume, extract its GitHub URL, and return structured project JSON:

```bash
.venv/bin/python -m cli.github.parse_github ./resume.pdf
```

Useful options:

```bash
.venv/bin/python -m cli.github.parse_github ./resume.pdf \
  --output-file github_projects.json \
  --llm-max-workers 8 \
  --max-repos 50 \
  --readme-only
```

Parse a GitHub profile URL directly (dev script):

```bash
.venv/bin/python -m app.modules.github.test https://github.com/your-username \
  --output-file github_projects.json \
  --llm-max-workers 8
```

## Logging

Logging is configured centrally through `app/core/logger.py`. Modules emit structured INFO/WARNING/ERROR logs during parsing and LLM routing.

Environment variables:

```bash
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

If `LOG_FILE` is unset, logs go to stderr only.
