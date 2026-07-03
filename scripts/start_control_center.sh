#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON="$REPO_ROOT/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  printf '[FAIL] .venv not found. Run setup first:\n' >&2
  printf 'bash scripts/setup_control_center.sh\n' >&2
  exit 1
fi

printf 'Starting MathModel Control Center...\n'
printf 'Frontend: http://127.0.0.1:5173\n'
printf 'Backend:  http://127.0.0.1:8000\n'
printf 'Press Ctrl+C to stop both services.\n\n'

start_frontend() {
  cd "$REPO_ROOT/app/frontend"
  if command -v pnpm >/dev/null 2>&1; then
    pnpm run dev
  elif command -v corepack >/dev/null 2>&1 && [ -f pnpm-lock.yaml ]; then
    corepack pnpm run dev
  else
    npm run dev
  fi
}

(cd "$REPO_ROOT/app/backend" && "$PYTHON" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000) &
BACKEND_PID=$!

start_frontend &
FRONTEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" >/dev/null 2>&1 || true
}

trap cleanup INT TERM EXIT
wait
