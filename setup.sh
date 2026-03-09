#!/usr/bin/env bash
# Resume Helper — Linux/macOS local development setup
# Run from the project root: bash setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"

echo "=== Resume Helper Setup ==="

# ── 1. Python virtual environment ──────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "[1/6] Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "[1/6] Virtual environment already exists, skipping."
fi

echo "[2/6] Activating virtual environment..."
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ── 2. Install Python dependencies ─────────────────────────────────────────
echo "[3/6] Installing Python dependencies..."
pip install --upgrade pip
pip install -r "$BACKEND_DIR/requirements.txt"

# ── 3. Download spaCy model ─────────────────────────────────────────────────
echo "[4/6] Downloading spaCy language model (en_core_web_lg)..."
python -m spacy download en_core_web_lg

# ── 4. Generate backend/.env if missing ────────────────────────────────────
ENV_FILE="$BACKEND_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "[5/6] Generating backend/.env with fresh keys..."
    FERNET_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    JWT_SECRET=$(python -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())")
    cat > "$ENV_FILE" <<EOF
# Local development environment — do NOT commit this file
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/resume_helper
JWT_SECRET_KEY=${JWT_SECRET}
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434
AES_ENCRYPTION_KEY=${FERNET_KEY}
CORS_ORIGINS=["http://localhost:3000"]
EOF
    echo "    Created $ENV_FILE"
else
    echo "[5/6] backend/.env already exists, skipping key generation."
fi

# ── 5. Install frontend dependencies ──────────────────────────────────────
echo "[6/6] Installing frontend Node dependencies..."
cd "$FRONTEND_DIR" && npm install && cd "$SCRIPT_DIR"

# ── Done ───────────────────────────────────────────────────────────────────
echo ""
echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "  1. Start PostgreSQL (or run Docker Compose):  docker compose up -d db"
echo "  2. Start Ollama with Llama 3:                 ollama run llama3"
echo "  3. Run database migrations:                   cd backend && alembic upgrade head"
echo "  4. Start the backend API:                     cd backend && uvicorn app.main:app --reload"
echo "  5. Start the frontend:                        cd frontend && npm run dev"
echo "  6. Run tests:                                 cd backend && pytest"
echo ""
