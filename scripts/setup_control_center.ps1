$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "app\backend"
$FrontendDir = Join-Path $RepoRoot "app\frontend"
$VenvDir = Join-Path $RepoRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$EnvExample = Join-Path $RepoRoot ".env.example"
$EnvFile = Join-Path $RepoRoot ".env"

function Write-Step($Message) {
  Write-Host ""
  Write-Host "==> $Message" -ForegroundColor Cyan
}

function Fail($Message) {
  Write-Host "[FAIL] $Message" -ForegroundColor Red
  exit 1
}

function Invoke-Checked($FilePath, [string[]]$Arguments, $FailureMessage) {
  & $FilePath @Arguments
  if ($LASTEXITCODE -ne 0) {
    Fail $FailureMessage
  }
}

function Ensure-Command($Name, $InstallHint) {
  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  if (-not $cmd) {
    Fail "$Name was not found. $InstallHint"
  }
  return $cmd.Source
}

function Ensure-EnvExampleEntry($Key, $Line) {
  if (-not (Test-Path -LiteralPath $EnvExample)) {
    @(
      "# MathModelAgent local environment template",
      "# provider=none does not need any API key.",
      "# Real DeepSeek / OpenAI-compatible calls need backend environment variables.",
      "# Do not paste API keys into the browser frontend.",
      ""
    ) | Set-Content -LiteralPath $EnvExample -Encoding UTF8
  }
  $content = Get-Content -LiteralPath $EnvExample -Raw -Encoding UTF8
  if ($content -notmatch "(?m)^$([regex]::Escape($Key))=") {
    Add-Content -LiteralPath $EnvExample -Encoding UTF8 -Value $Line
  }
}

Set-Location -LiteralPath $RepoRoot

Write-Step "Checking Python"
$Python = Ensure-Command "python" "Install Python 3.10+ and reopen PowerShell."
$PythonVersion = & $Python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
$PythonPath = & $Python -c "import sys; print(sys.executable)"
Write-Host "[OK] Python $PythonVersion"
Write-Host "     $PythonPath"
if ([version]$PythonVersion -lt [version]"3.10.0") {
  Fail "Python >= 3.10 is required."
}

Write-Step "Checking Node.js"
$Node = Ensure-Command "node" "Install Node.js LTS 18+ and reopen PowerShell."
$Npm = Ensure-Command "npm" "npm should be installed with Node.js LTS."
$NodeVersionText = (& $Node --version).Trim()
$NodeVersion = $NodeVersionText.TrimStart("v")
$NpmVersion = (& $Npm --version).Trim()
Write-Host "[OK] Node $NodeVersionText"
Write-Host "[OK] npm $NpmVersion"
if ([version]$NodeVersion -lt [version]"18.0.0") {
  Fail "Node.js >= 18 is required. Please install Node.js LTS."
}

Write-Step "Creating Python virtual environment"
if (Test-Path -LiteralPath $VenvPython) {
  Write-Host "[OK] Existing .venv found: $VenvDir"
} else {
  Invoke-Checked $Python @("-m", "venv", $VenvDir) "Failed to create .venv."
  Write-Host "[OK] Created .venv: $VenvDir"
}

Write-Step "Installing backend dependencies"
Invoke-Checked $VenvPython @("-m", "pip", "install", "-r", (Join-Path $BackendDir "requirements.txt")) "Failed to install backend requirements."
$LangGraphReq = Join-Path $BackendDir "requirements-langgraph.txt"
if (Test-Path -LiteralPath $LangGraphReq) {
  Invoke-Checked $VenvPython @("-m", "pip", "install", "-r", $LangGraphReq) "Failed to install LangGraph requirements."
}

Write-Step "Installing frontend dependencies"
Set-Location -LiteralPath $FrontendDir
$PnpmCommand = Get-Command "pnpm" -ErrorAction SilentlyContinue
$CorepackCommand = Get-Command "corepack" -ErrorAction SilentlyContinue
if ($PnpmCommand) {
  Invoke-Checked $PnpmCommand.Source @("install") "Failed to install frontend dependencies with pnpm."
} elseif ($CorepackCommand -and (Test-Path -LiteralPath (Join-Path $FrontendDir "pnpm-lock.yaml"))) {
  Invoke-Checked $CorepackCommand.Source @("pnpm", "install") "Failed to install frontend dependencies with corepack pnpm."
} else {
  & $Npm install
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] npm install failed. Retrying with --legacy-peer-deps for npm peer dependency resolution." -ForegroundColor Yellow
    & $Npm install --legacy-peer-deps
    if ($LASTEXITCODE -ne 0) {
      Fail "Failed to install frontend dependencies."
    }
  }
}
Set-Location -LiteralPath $RepoRoot

Write-Step "Ensuring .env.example"
Ensure-EnvExampleEntry "DEEPSEEK_API_KEY" "DEEPSEEK_API_KEY="
Ensure-EnvExampleEntry "OPENAI_API_KEY" "OPENAI_API_KEY="
Ensure-EnvExampleEntry "OPENAI_BASE_URL" "OPENAI_BASE_URL="
Ensure-EnvExampleEntry "MATHMODEL_WORKSPACE_ROOT" "MATHMODEL_WORKSPACE_ROOT=workspaces"
Write-Host "[OK] .env.example is ready."
if (-not (Test-Path -LiteralPath $EnvFile)) {
  Write-Host "[WARN] .env not found. provider=none can run now; for real API calls, copy .env.example to .env and fill keys."
}

Write-Step "Running doctor"
Invoke-Checked $VenvPython @((Join-Path $RepoRoot "scripts\doctor_control_center.py")) "Doctor reported a blocked setup."

Write-Host ""
Write-Host "Setup complete."
Write-Host "Start Control Center with:"
Write-Host "powershell -ExecutionPolicy Bypass -File scripts/start_control_center.ps1"
