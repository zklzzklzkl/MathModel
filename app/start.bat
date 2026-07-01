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

echo [backend] Checking dependencies...
"%BACKEND_DIR%\.venv\Scripts\python.exe" -c "import fastapi, uvicorn, multipart" >nul 2>nul
if errorlevel 1 (
  echo [backend] Installing dependencies...
  "%BACKEND_DIR%\.venv\Scripts\python.exe" -m pip install -q --timeout 60 -r "%BACKEND_DIR%\requirements.txt"
  if errorlevel 1 (
    echo [backend] PyPI install failed. Retrying with Tsinghua mirror...
    "%BACKEND_DIR%\.venv\Scripts\python.exe" -m pip install -q --timeout 60 -i https://pypi.tuna.tsinghua.edu.cn/simple -r "%BACKEND_DIR%\requirements.txt"
    if errorlevel 1 (
      echo [backend] Dependency install failed. Check your network or run:
      echo cd /d "%BACKEND_DIR%"
      echo .venv\Scripts\python.exe -m pip install -r requirements.txt
      pause
      exit /b 1
    )
  )
) else (
  echo [backend] Dependencies already installed, skipping pip install.
)

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
