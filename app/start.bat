@echo off
chcp 65001 >nul
setlocal

set "APP_DIR=%~dp0"
set "BACKEND_DIR=%APP_DIR%backend"
set "FRONTEND_DIR=%APP_DIR%frontend"

echo ==============================================
echo  MathModel Control Center
echo  Backend:  http://127.0.0.1:8000
echo  Frontend: http://127.0.0.1:5173
echo ==============================================
echo.

if not exist "%BACKEND_DIR%\.venv\Scripts\python.exe" (
  echo [backend] Creating virtual environment...
  python -m venv "%BACKEND_DIR%\.venv"
)

echo [backend] Installing dependencies...
"%BACKEND_DIR%\.venv\Scripts\python.exe" -m pip install -q -r "%BACKEND_DIR%\requirements.txt"

if not exist "%FRONTEND_DIR%\node_modules" (
  echo [frontend] Installing dependencies...
  pushd "%FRONTEND_DIR%"
  pnpm install
  popd
)

start "MathModel Control Backend" cmd /k "cd /d ""%BACKEND_DIR%"" && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
start "MathModel Control Frontend" cmd /k "cd /d ""%FRONTEND_DIR%"" && pnpm dev"

echo Services are starting. Open http://127.0.0.1:5173
echo.
pause
