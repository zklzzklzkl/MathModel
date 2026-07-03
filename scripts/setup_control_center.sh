#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/app/backend"
FRONTEND_DIR="$REPO_ROOT/app/frontend"
VENV_DIR="$REPO_ROOT/.venv"
ENV_EXAMPLE="$REPO_ROOT/.env.example"

log() {
  printf '\n==> %s\n' "$1"
}

fail() {
  printf '[FAIL] %s\n' "$1" >&2
  exit 1
}

command -v python3 >/dev/null 2>&1 || fail "python3 was not found. Install Python 3.10+."
command -v node >/dev/null 2>&1 || fail "node was not found. Install Node.js LTS 18+."
command -v npm >/dev/null 2>&1 || fail "npm was not found. Install Node.js LTS 18+."

log "Checking Python"
PY_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' || fail "Python >= 3.10 is required."
printf '[OK] Python %s\n' "$PY_VERSION"

log "Checking Node.js"
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
if [ "$NODE_MAJOR" -lt 18 ]; then
  fail "Node.js >= 18 is required. Install Node.js LTS."
fi
printf '[OK] Node %s\n' "$(node --version)"
printf '[OK] npm %s\n' "$(npm --version)"

log "Creating Python virtual environment"
if [ -x "$VENV_DIR/bin/python" ]; then
  printf '[OK] Existing .venv found: %s\n' "$VENV_DIR"
else
  python3 -m venv "$VENV_DIR"
  printf '[OK] Created .venv: %s\n' "$VENV_DIR"
fi

log "Installing backend dependencies"
"$VENV_DIR/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt"
if [ -f "$BACKEND_DIR/requirements-langgraph.txt" ]; then
  "$VENV_DIR/bin/python" -m pip install -r "$BACKEND_DIR/requirements-langgraph.txt"
fi

log "Installing frontend dependencies"
if command -v pnpm >/dev/null 2>&1; then
  (cd "$FRONTEND_DIR" && pnpm install)
elif command -v corepack >/dev/null 2>&1 && [ -f "$FRONTEND_DIR/pnpm-lock.yaml" ]; then
  (cd "$FRONTEND_DIR" && corepack pnpm install)
elif ! (cd "$FRONTEND_DIR" && npm install); then
  printf '[WARN] npm install failed. Retrying with --legacy-peer-deps.\n'
  (cd "$FRONTEND_DIR" && npm install --legacy-peer-deps)
fi

log "Ensuring .env.example"
if [ ! -f "$ENV_EXAMPLE" ]; then
  cat > "$ENV_EXAMPLE" <<'EOF'
# MathModelAgent local environment template
# provider=none does not need any API key.
# Real DeepSeek / OpenAI-compatible calls need backend environment variables.
# Do not paste API keys into the browser frontend.

DEEPSEEK_API_KEY=
OPENAI_API_KEY=
OPENAI_BASE_URL=
MATHMODEL_WORKSPACE_ROOT=workspaces
EOF
fi
for key in DEEPSEEK_API_KEY OPENAI_API_KEY OPENAI_BASE_URL MATHMODEL_WORKSPACE_ROOT; do
  if ! grep -q "^${key}=" "$ENV_EXAMPLE"; then
    if [ "$key" = "MATHMODEL_WORKSPACE_ROOT" ]; then
      printf '%s=workspaces\n' "$key" >> "$ENV_EXAMPLE"
    else
      printf '%s=\n' "$key" >> "$ENV_EXAMPLE"
    fi
  fi
done

if [ ! -f "$REPO_ROOT/.env" ]; then
  printf '[WARN] .env not found. provider=none can run now; copy .env.example to .env for real API calls.\n'
fi

log "Running doctor"
"$VENV_DIR/bin/python" "$REPO_ROOT/scripts/doctor_control_center.py"

printf '\nSetup complete.\n'
printf 'Start Control Center with: bash scripts/start_control_center.sh\n'
