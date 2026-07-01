# MathModel Control Backend

FastAPI backend for the MathModelAgent V2.3 Control Center.

## Run

```powershell
cd D:\WorkSpace_MathModel\app\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend reads the parent repository by default. Override paths with `.env`:

```text
MATHMODEL_ROOT=D:\WorkSpace_MathModel
WORKSPACE_ROOT=D:\WorkSpace_MathModel\workspaces
EXAMPLES_ROOT=D:\WorkSpace_MathModel\examples
```
