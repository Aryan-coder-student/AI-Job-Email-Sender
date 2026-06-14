#!/usr/bin/env bash
# End-to-end pipeline smoke test using the project CLIs and data/ inputs.
#
# Defaults:
#   resume    -> data/AryanPahari.pdf
#   companies -> data/companies_sheet.json
#   company   -> 10up
#
# Usage:
#   ./scripts/run_pipeline.sh
#   ./scripts/run_pipeline.sh --from-step 5 --dry-run
#   ./scripts/run_pipeline.sh --company "100Starlings" --dry-run
#   ./scripts/run_pipeline.sh --skip-services --skip-enrichment --max-repos 5
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PYTHON="${ROOT}/.venv/bin/python"
else
  PYTHON="python3"
fi

RESUME="${RESUME:-${ROOT}/data/AryanPahari.pdf}"
COMPANIES="${COMPANIES:-${ROOT}/data/companies_sheet.json}"
COMPANY="${COMPANY:-10up}"
OUTPUT_DIR="${OUTPUT_DIR:-${ROOT}/data}"

PARSED_RESUME="${OUTPUT_DIR}/parse_resume.json"
GITHUB_PROJECTS="${OUTPUT_DIR}/github_projects_resume.json"
GRAPH_RESULT="${OUTPUT_DIR}/graph_build.json"
MATCHES="${OUTPUT_DIR}/matches.json"
DRAFT="${OUTPUT_DIR}/draft.json"
MAIL_RESULT="${OUTPUT_DIR}/mail_queue_result.json"

SKIP_SERVICES=0
SKIP_ENRICHMENT=0
DRY_RUN=0
NO_ENQUEUE=0
MAX_REPOS=100
MAX_COMPANIES=25
CLEAR_GRAPH=0
RECIPIENT_EMAIL=""
FROM_STEP=1

usage() {
  cat <<'EOF'
End-to-end pipeline smoke test using the project CLIs and data/ inputs.

Steps:
  1  Parse resume
  2  Parse GitHub projects
  3  Build knowledge graph + vector indexes
  4  Rank projects for company
  5  Generate application email draft
  6  Process email queue

Defaults:
  resume    -> data/AryanPahari.pdf
  companies -> data/companies_sheet.json
  company   -> 10up

Examples:
  ./scripts/run_pipeline.sh
  ./scripts/run_pipeline.sh --from-step 5 --dry-run
  ./scripts/run_pipeline.sh --company "100Starlings" --dry-run
  ./scripts/run_pipeline.sh --skip-services --skip-enrichment --max-repos 5
EOF
  echo
  echo "Options:"
  echo "  --from-step N          Start at step N (1-6); earlier steps are skipped"
  echo "  --resume PATH          Resume PDF/DOCX/TXT (default: data/AryanPahari.pdf)"
  echo "  --companies PATH       Parsed companies JSON (default: data/companies_sheet.json)"
  echo "  --company NAME         Company to rank/draft for (default: 10up)"
  echo "  --recipient-email ADDR Draft recipient (default: first email from resume)"
  echo "  --output-dir PATH      Where to write step outputs (default: data/)"
  echo "  --max-repos N          GitHub repos to inspect (default: 100)"
  echo "  --max-companies N      Companies indexed in graph step (default: 25)"
  echo "  --skip-services        Skip Neo4j/Qdrant readiness checks"
  echo "  --skip-enrichment      Skip LLM graph enrichment"
  echo "  --clear-graph          Clear Neo4j before graph build"
  echo "  --dry-run              Do not send emails; mail step uses --dry-run"
  echo "  --no-enqueue           Generate draft without pushing to Redis"
  echo "  -h, --help             Show this help"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from-step) FROM_STEP="$2"; shift 2 ;;
    --resume) RESUME="$2"; shift 2 ;;
    --companies) COMPANIES="$2"; shift 2 ;;
    --company) COMPANY="$2"; shift 2 ;;
    --recipient-email) RECIPIENT_EMAIL="$2"; shift 2 ;;
    --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
    --max-repos) MAX_REPOS="$2"; shift 2 ;;
    --max-companies) MAX_COMPANIES="$2"; shift 2 ;;
    --skip-services) SKIP_SERVICES=1; shift ;;
    --skip-enrichment) SKIP_ENRICHMENT=1; shift ;;
    --clear-graph) CLEAR_GRAPH=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --no-enqueue) NO_ENQUEUE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if ! [[ "$FROM_STEP" =~ ^[1-6]$ ]]; then
  echo "--from-step must be an integer from 1 to 6 (got: ${FROM_STEP})" >&2
  exit 1
fi

PARSED_RESUME="${OUTPUT_DIR}/parse_resume.json"
GITHUB_PROJECTS="${OUTPUT_DIR}/github_projects_resume.json"
GRAPH_RESULT="${OUTPUT_DIR}/graph_build.json"
MATCHES="${OUTPUT_DIR}/matches.json"
DRAFT="${OUTPUT_DIR}/draft.json"
MAIL_RESULT="${OUTPUT_DIR}/mail_queue_result.json"

require_file() {
  if [[ ! -f "$1" ]]; then
    echo "Missing required file: $1" >&2
    echo "Run earlier pipeline steps first or lower --from-step." >&2
    exit 1
  fi
}

run_step() {
  local title="$1"
  shift
  echo
  echo "==> ${title}"
  "$@"
}

resolve_recipient_email() {
  if [[ -n "$RECIPIENT_EMAIL" ]]; then
    return
  fi

  RECIPIENT_EMAIL="$("$PYTHON" - <<PY
import json
from pathlib import Path

company_name = """${COMPANY}"""
companies_path = Path("""${COMPANIES}""")
resume_path = Path("""${PARSED_RESUME}""")

companies = json.loads(companies_path.read_text(encoding="utf-8"))
resume = json.loads(resume_path.read_text(encoding="utf-8"))

for record in companies:
    if str(record.get("company_name") or "").strip().lower() == company_name.strip().lower():
        hr_email = str(record.get("hr_email") or "").strip()
        if hr_email:
            print(hr_email)
            raise SystemExit(0)

emails = resume.get("links", {}).get("emails") or []
for email in emails:
    cleaned = str(email).strip()
    if cleaned:
        print(cleaned)
        raise SystemExit(0)

raise SystemExit("No recipient email found. Pass --recipient-email or ensure resume links.emails is populated.")
PY
)"
  echo "Using recipient email: ${RECIPIENT_EMAIL}"
}

load_candidate_id() {
  CANDIDATE_ID="$("$PYTHON" - <<PY
import json
from pathlib import Path

payload = json.loads(Path("${GRAPH_RESULT}").read_text(encoding="utf-8"))
print(payload["candidate"]["metadata"]["candidate_id"])
PY
)"
}

require_file "$COMPANIES"
mkdir -p "$OUTPUT_DIR"

if [[ "$FROM_STEP" -le 2 ]]; then
  require_file "$RESUME"
fi
if [[ "$FROM_STEP" -ge 3 ]]; then
  require_file "$PARSED_RESUME"
  require_file "$GITHUB_PROJECTS"
fi
if [[ "$FROM_STEP" -ge 4 ]]; then
  require_file "$GRAPH_RESULT"
fi
if [[ "$FROM_STEP" -ge 5 ]]; then
  require_file "$MATCHES"
  require_file "$GITHUB_PROJECTS"
fi

if [[ "$FROM_STEP" -le 4 && "$SKIP_SERVICES" -eq 0 ]]; then
  run_step "Waiting for Neo4j and Qdrant" "${ROOT}/scripts/wait_for_services.sh"
fi

if [[ "$FROM_STEP" -le 1 ]]; then
  run_step "1/6 Parse resume" \
    "$PYTHON" -m cli.resume.parse_resume "$RESUME" --output-file "$PARSED_RESUME"
fi

if [[ "$FROM_STEP" -le 2 ]]; then
  run_step "2/6 Parse GitHub projects from resume" \
    "$PYTHON" -m cli.github.parse_github "$RESUME" \
      --max-repos "$MAX_REPOS" \
      --output-file "$GITHUB_PROJECTS"
fi

if [[ "$FROM_STEP" -le 3 ]]; then
  GRAPH_ARGS=(
    --resume "$PARSED_RESUME"
    --github "$GITHUB_PROJECTS"
    --companies "$COMPANIES"
    --max-companies "$MAX_COMPANIES"
    --output-file "$GRAPH_RESULT"
  )
  if [[ "$SKIP_ENRICHMENT" -eq 1 ]]; then
    GRAPH_ARGS+=(--skip-enrichment)
  fi
  if [[ "$CLEAR_GRAPH" -eq 1 ]]; then
    GRAPH_ARGS+=(--clear)
  fi

  run_step "3/6 Build knowledge graph + vector indexes" \
    "$PYTHON" -m cli.graph.build_graph "${GRAPH_ARGS[@]}"
fi

if [[ "$FROM_STEP" -le 4 ]]; then
  load_candidate_id
  run_step "4/6 Rank projects for ${COMPANY} (${CANDIDATE_ID})" \
    "$PYTHON" -m cli.matching.rank_projects \
      --companies "$COMPANIES" \
      --company "$COMPANY" \
      --candidate-id "$CANDIDATE_ID" \
      --output-file "$MATCHES"
fi

if [[ "$FROM_STEP" -le 5 ]]; then
  resolve_recipient_email

  DRAFT_ARGS=(
    --resume "$PARSED_RESUME"
    --matches "$MATCHES"
    --github "$GITHUB_PROJECTS"
    --companies "$COMPANIES"
    --company "$COMPANY"
    --recipient-email "$RECIPIENT_EMAIL"
    --output-file "$DRAFT"
  )
  if [[ "$NO_ENQUEUE" -eq 1 ]]; then
    DRAFT_ARGS+=(--no-enqueue)
  fi

  run_step "5/6 Generate application email draft" \
    "$PYTHON" -m cli.emails.generate_draft "${DRAFT_ARGS[@]}"
fi

if [[ "$FROM_STEP" -le 6 ]]; then
  MAIL_ARGS=(--output-file "$MAIL_RESULT")
  if [[ "$DRY_RUN" -eq 1 ]]; then
    MAIL_ARGS+=(--dry-run)
  fi

  run_step "6/6 Process email queue" \
    "$PYTHON" -m cli.mail.process_queue "${MAIL_ARGS[@]}"
fi

echo
echo "Pipeline finished (from step ${FROM_STEP})."
echo "  resume parsed:  ${PARSED_RESUME}"
echo "  github parsed:  ${GITHUB_PROJECTS}"
echo "  graph result:   ${GRAPH_RESULT}"
echo "  matches:        ${MATCHES}"
echo "  draft:          ${DRAFT}"
echo "  mail result:    ${MAIL_RESULT}"
