from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Resume Helper API",
    description="Multi-Agent AI Resume Orchestration Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────────────
from app.api.auth import router as auth_router  # noqa: E402
from app.api.jobs import router as jobs_router  # noqa: E402
from app.api.resumes import router as resumes_router  # noqa: E402

app.include_router(auth_router)
app.include_router(resumes_router)
app.include_router(jobs_router)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}
