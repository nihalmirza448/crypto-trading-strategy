#!/usr/bin/env bash
# Publish paymyrent dashboard snapshot (local JSON + optional Vercel ingest).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv311/bin/python" ]]; then
  PY="$ROOT/.venv311/bin/python"
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
else
  PY="$(command -v python3)"
fi

echo "Using: $PY"
exec "$PY" -m forward_test.publish_snapshot
