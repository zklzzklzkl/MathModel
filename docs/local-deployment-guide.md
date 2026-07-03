# Local Deployment Guide

## For Beginners

MathModelAgent Control Center v2 has two local services:

- Backend: FastAPI. It reads workspaces, runs LangGraph, audits artifacts and generates reports.
- Frontend: Vue/Vite. It provides the browser interface.

You do not need Docker for the default local setup.

## Windows One-click Setup

Run this from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_control_center.ps1
```

The setup script checks Python and Node.js, creates `.venv`, installs backend and frontend dependencies, prepares `.env.example`, and runs the doctor.

## Windows One-click Start

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_control_center.ps1
```

This opens two PowerShell windows:

- `MathModel Backend`
- `MathModel Frontend`

Close those windows to stop the services.

## macOS / Linux

```bash
bash scripts/setup_control_center.sh
bash scripts/start_control_center.sh
```

## Open the App

Open:

```text
http://127.0.0.1:5173
```

Backend health endpoint:

```text
http://127.0.0.1:8000/api/health
```

## No API Key Mode

`provider=none` does not need an API key. It does not call real models and does not create model-call costs. It is used to verify the workflow, safety boundaries and artifact chain.

## Real API Mode

Real DeepSeek / OpenAI-compatible calls need API keys.

Copy:

```text
.env.example -> .env
```

Fill only backend environment variables:

```env
DEEPSEEK_API_KEY=
```

or:

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=
```

Paste real keys only into your private local `.env` or shell environment. API keys should stay in the backend environment. Do not paste API keys into the browser page. Restart the backend after changing `.env`.

## Troubleshooting

### PowerShell blocks scripts

Use:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_control_center.ps1
```

### npm install is slow

You may use a local or regional npm mirror if you already trust it. The setup script does not force npm registry changes.

### Port 8000 or 5173 is occupied

Close the process using that port, or edit the start script ports manually.

### LangGraph unavailable

Run setup again and confirm `app/backend/requirements-langgraph.txt` installed successfully:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_control_center.ps1
```

### provider=none vs real API

`provider=none` verifies workflow and safety boundaries. It does not represent real LLM modeling quality. Use DeepSeek / OpenAI-compatible providers only after API keys are configured in backend environment variables.

### Frontend opens but backend connection fails

Confirm the backend window is running, then open:

```text
http://127.0.0.1:8000/api/health
```

## Script Safety

The setup/start scripts are designed to:

- not delete user files
- not overwrite `.env`
- not write real API keys
- not execute remote downloaded scripts
- not modify system `PATH`
- not install Python or Node.js for you
- not require administrator privileges
- print clear errors when a command fails

## Validation

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_control_center.ps1
python scripts/doctor_control_center.py
cd app/frontend
npm run build
cd ../..
python -m pytest tests/test_langgraph_api.py -q
python -m pytest tests/test_safe_langgraph_benchmark_api.py -q
git diff --check
git status --short --branch
```
