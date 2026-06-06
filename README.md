# Job Send Crawl

## Setup

Run the project setup script:

```bash
./setup_uv_env.sh
```

The script installs `uv` if needed, creates `.venv`, and installs runtime plus test dependencies.

Run Excel module tests:

```bash
.venv/bin/python -m pytest tests/modules/excel
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

By default, the parser skips rows where 90% or more cells are empty. For noisy sheets,
lower the threshold, for example `--max-empty-ratio 0.75`. To keep sparse rows, use
`--keep-sparse-rows`.

## LLM Router

Environment variables:

```bash
GROQ_API_KEY=
GROQ_MODEL=
OPENAI_API_KEY=
OPENAI_MODEL=
GEMINI_API_KEY=
GEMINI_MODEL=
```

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

Provider order is Groq, OpenAI, then Gemini. If a provider returns a rate-limit response,
the router pauses it temporarily and tries the next provider.
