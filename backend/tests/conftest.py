"""Shared test fixtures for the Resume Helper backend."""

from __future__ import annotations

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password

# ---------------------------------------------------------------------------
# In-memory SQLite engine for testing
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
_TestSessionFactory = async_sessionmaker(
    _engine, class_=AsyncSession, expire_on_commit=False
)


# ---------------------------------------------------------------------------
# Override settings BEFORE the app is loaded
# ---------------------------------------------------------------------------

import app.config as _cfg  # noqa: E402

_cfg.settings.DATABASE_URL = TEST_DATABASE_URL
_cfg.settings.JWT_SECRET_KEY = "test-secret-key-that-is-at-least-32-chars-long!"
_cfg.settings.JWT_ALGORITHM = "HS256"
_cfg.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
_cfg.settings.OPENAI_API_KEY = ""
_cfg.settings.ANTHROPIC_API_KEY = ""
_cfg.settings.AES_ENCRYPTION_KEY = Fernet.generate_key().decode()

# Reset the fernet singleton so it picks up the test key
import app.services.encryption_service as _enc_mod  # noqa: E402

_enc_mod._fernet = None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def _create_tables():
    """Create all tables before each test and drop after."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async DB session scoped to a single test."""
    async with _TestSessionFactory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client wired to the FastAPI app with the test DB."""
    from app.main import app

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Insert a test user into the database and return it."""
    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict[str, str]:
    """Return Authorization headers with a valid JWT for *test_user*."""
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}
