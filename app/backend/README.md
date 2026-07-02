# MathModel Control Backend

FastAPI backend for the MathModelAgent V2.6 Control Center.

## Run

```powershell
cd app/backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend reads the parent repository by default. Override paths with `.env`:

```text
MATHMODEL_ROOT=<repo-root>
WORKSPACE_ROOT=<repo-root>/workspaces
EXAMPLES_ROOT=<repo-root>/examples
```
