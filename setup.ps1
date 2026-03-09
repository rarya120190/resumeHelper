#!/usr/bin/env pwsh
# Resume Helper — Windows local development setup
# Run from the project root: .\setup.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=== Resume Helper Setup ===" -ForegroundColor Cyan

# ── 1. Python virtual environment ──────────────────────────────────────────
$venvPath = Join-Path $PSScriptRoot "backend\venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "[1/6] Creating Python virtual environment..." -ForegroundColor Yellow
    py -m venv $venvPath
} else {
    Write-Host "[1/6] Virtual environment already exists, skipping." -ForegroundColor Green
}

$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
Write-Host "[2/6] Activating virtual environment..." -ForegroundColor Yellow
& $activateScript

# ── 2. Install Python dependencies ─────────────────────────────────────────
Write-Host "[3/6] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r (Join-Path $PSScriptRoot "backend\requirements.txt")

# ── 3. Download spaCy model ─────────────────────────────────────────────────
Write-Host "[4/6] Downloading spaCy language model (en_core_web_lg)..." -ForegroundColor Yellow
python -m spacy download en_core_web_lg

# ── 4. Generate backend/.env if missing ────────────────────────────────────
$envFile = Join-Path $PSScriptRoot "backend\.env"
if (-not (Test-Path $envFile)) {
    Write-Host "[5/6] Generating backend/.env with fresh keys..." -ForegroundColor Yellow
    $fernetKey  = python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    $jwtSecret  = python -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
    @"
# Local development environment — do NOT commit this file
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/resume_helper
JWT_SECRET_KEY=$jwtSecret
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434
AES_ENCRYPTION_KEY=$fernetKey
CORS_ORIGINS=["http://localhost:3000"]
"@ | Out-File -FilePath $envFile -Encoding utf8
    Write-Host "    Created $envFile" -ForegroundColor Green
} else {
    Write-Host "[5/6] backend/.env already exists, skipping key generation." -ForegroundColor Green
}

# ── 5. Install frontend dependencies ──────────────────────────────────────
Write-Host "[6/6] Installing frontend Node dependencies..." -ForegroundColor Yellow
Push-Location (Join-Path $PSScriptRoot "frontend")
npm install
Pop-Location

# ── Done ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=== Setup complete! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Start PostgreSQL (or run Docker Compose):  docker compose up -d db" -ForegroundColor Gray
Write-Host "  2. Start Ollama with Llama 3:                 ollama run llama3" -ForegroundColor Gray
Write-Host "  3. Run database migrations:                   cd backend && alembic upgrade head" -ForegroundColor Gray
Write-Host "  4. Start the backend API:                     cd backend && uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host "  5. Start the frontend:                        cd frontend && npm run dev" -ForegroundColor Gray
Write-Host "  6. Run tests:                                 cd backend && pytest" -ForegroundColor Gray
Write-Host ""
