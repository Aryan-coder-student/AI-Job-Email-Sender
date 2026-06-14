#!/usr/bin/env bash
set -euo pipefail

NEO4J_URI="${NEO4J_URI:-bolt://localhost:7687}"
QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-30}"
SLEEP_SECONDS="${SLEEP_SECONDS:-2}"

wait_for_http() {
  local url="$1"
  local name="$2"
  local attempt=1

  until curl -sf "$url" >/dev/null; do
    if (( attempt >= MAX_ATTEMPTS )); then
      echo "Timed out waiting for ${name} at ${url}" >&2
      exit 1
    fi
    echo "Waiting for ${name} (${attempt}/${MAX_ATTEMPTS})..."
    attempt=$((attempt + 1))
    sleep "$SLEEP_SECONDS"
  done
  echo "${name} is ready."
}

wait_for_http "${QDRANT_URL}/readyz" "Qdrant"

python3 - <<'PY'
import os
import sys
import time

from neo4j import GraphDatabase

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "changeme")
max_attempts = int(os.getenv("MAX_ATTEMPTS", "30"))
sleep_seconds = int(os.getenv("SLEEP_SECONDS", "2"))

for attempt in range(1, max_attempts + 1):
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        driver.close()
        print("Neo4j is ready.")
        sys.exit(0)
    except Exception as error:
        if attempt >= max_attempts:
            print(f"Timed out waiting for Neo4j at {uri}: {error}", file=sys.stderr)
            sys.exit(1)
        print(f"Waiting for Neo4j ({attempt}/{max_attempts})...")
        time.sleep(sleep_seconds)
PY
