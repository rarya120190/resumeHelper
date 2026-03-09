# Resume Helper — Multi-Agent AI Resume Orchestration Platform

Resume Helper is a tool for building ATS-optimized resumes with multiple AI agents working together to tailor your resume to specific job descriptions, ensuring factual fidelity and privacy.

## Architecture

- **Frontend**: Next.js 14 (React), Tailwind CSS
- **Backend**: Python (FastAPI)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI Orchestration**: LangGraph
- **PDF Rendering**: WeasyPrint
- **Security**: OAuth 2.0, AES-256, Microsoft Presidio (PII masking)

## AI Agent Pipeline

1. **JD Normalizer** (Llama 3) — Extracts structured JSON from job descriptions
2. **Company Enrichment Agent** (Llama 3) — Researches company data for context
3. **Resume Writer Agent** (GPT-4o / Claude 3.5) — Tailors resume using STAR method
4. **QA Auditor Agent** — Validates factual integrity (strict subset rule)
5. **Dynamic Rulebook Agent** — Learns user style preferences over time

## Getting Started

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Run Tests
```bash
# Backend tests
cd backend
pytest --cov=app tests/

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## Environment Variables

Copy `.env.example` to `.env` and fill in values:
- `DATABASE_URL` — PostgreSQL connection string
- `OPENAI_API_KEY` — For GPT-4o resume writer
- `ANTHROPIC_API_KEY` — For Claude 3.5 alternative
- `OLLAMA_BASE_URL` — For local Llama 3 models
- `JWT_SECRET_KEY` — Auth token signing
- `AES_ENCRYPTION_KEY` — Data encryption at rest

## License

MIT
