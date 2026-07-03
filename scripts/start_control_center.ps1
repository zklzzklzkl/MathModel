$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "app\backend"
$FrontendDir = Join-Path $RepoRoot "app\frontend"
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"

function Quote-PS($Value) {
  return "'" + ($Value -replace "'", "''") + "'"
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
  Write-Host "[FAIL] .venv not found." -ForegroundColor Red
  Write-Host "Run setup first:"
  Write-Host "powershell -ExecutionPolicy Bypass -File scripts/setup_control_center.ps1"
  exit 1
}

if (-not (Test-Path -LiteralPath (Join-Path $FrontendDir "node_modules"))) {
  Write-Host "[WARN] app/frontend/node_modules not found. Run setup first if frontend fails."
}

$BackendCommand = @"
`$Host.UI.RawUI.WindowTitle = 'MathModel Backend'
Set-Location -LiteralPath $(Quote-PS $BackendDir)
& $(Quote-PS $VenvPython) -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"@

$FrontendCommand = @"
`$Host.UI.RawUI.WindowTitle = 'MathModel Frontend'
Set-Location -LiteralPath $(Quote-PS $FrontendDir)
if (Get-Command 'pnpm' -ErrorAction SilentlyContinue) {
  pnpm run dev
} elseif ((Get-Command 'corepack' -ErrorAction SilentlyContinue) -and (Test-Path -LiteralPath 'pnpm-lock.yaml')) {
  corepack pnpm run dev
} else {
  npm run dev
}
"@

Start-Process powershell -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $BackendCommand)
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $FrontendCommand)

Write-Host ""
Write-Host "MathModel Control Center is starting."
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host ""
Write-Host "Close the two PowerShell windows to stop the services."
