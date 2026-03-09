"""Tests for authentication endpoints (POST /auth/register, /auth/login, GET /auth/me)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.user import User


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "StrongPass1!",
                "full_name": "New User",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert "id" in data
        # Password must never leak in the response
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        resp = await client.post(
            "/auth/register",
            json={
                "email": test_user.email,
                "password": "AnotherPass1!",
                "full_name": "Dupe User",
            },
        )
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"].lower()

    async def test_register_invalid_email(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "StrongPass1!",
                "full_name": "Bad Email",
            },
        )
        assert resp.status_code == 422  # Pydantic validation error

    async def test_register_short_password(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={
                "email": "short@example.com",
                "password": "abc",
                "full_name": "Short PW",
            },
        )
        assert resp.status_code == 422

    async def test_register_missing_full_name(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={
                "email": "nofn@example.com",
                "password": "StrongPass1!",
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class TestLogin:
    async def test_login_success(self, client: AsyncClient, test_user: User):
        resp = await client.post(
            "/auth/login",
            json={"email": test_user.email, "password": "SecurePass123!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        resp = await client.post(
            "/auth/login",
            json={"email": test_user.email, "password": "WrongPassword!"},
        )
        assert resp.status_code == 401
        assert "invalid" in resp.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "Whatever1!"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


class TestGetMe:
    async def test_get_me_authenticated(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        resp = await client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["id"] == str(test_user.id)

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/auth/me")
        assert resp.status_code == 401

    async def test_get_me_invalid_token(self, client: AsyncClient):
        resp = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer totally.invalid.token"},
        )
        assert resp.status_code == 401

    async def test_get_me_expired_token_format(self, client: AsyncClient):
        """Malformed bearer value should 401."""
        resp = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer "},
        )
        assert resp.status_code == 401
