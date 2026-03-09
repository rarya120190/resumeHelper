"""Tests for resume endpoints (master + tailored)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import JobDescription
from app.models.resume import MasterResume, TailoredResume
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password


_MOCK_PIPELINE_RESULT = {
    "final_draft": "Tailored resume content here.",
    "qa_passed": True,
    "confidence_score": 92,
    "qa_result": {"status": "PASS", "violations": [], "confidence_score": 92},
    "jd_json": {},
    "company_context": None,
    "retry_count": 0,
    "error": None,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_master(client: AsyncClient, headers: dict, **overrides) -> dict:
    payload = {
        "title": overrides.get("title", "My Master Resume"),
        "content": overrides.get("content", "Full resume text here ..."),
    }
    resp = await client.post("/resumes/master", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()


async def _create_job(db: AsyncSession, user_id: uuid.UUID) -> JobDescription:
    job = JobDescription(
        user_id=user_id,
        raw_text="We are looking for a Senior Python Developer ...",
        company_name="Acme Corp",
        job_title="Senior Python Developer",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


# ---------------------------------------------------------------------------
# Master Resumes
# ---------------------------------------------------------------------------


class TestMasterResumes:
    async def test_create_master_resume(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        data = await _create_master(client, auth_headers)
        assert data["title"] == "My Master Resume"
        assert data["content"] == "Full resume text here ..."
        assert data["user_id"] == str(test_user.id)
        assert "id" in data
        assert "created_at" in data

    async def test_list_master_resumes(
        self, client: AsyncClient, auth_headers: dict
    ):
        await _create_master(client, auth_headers, title="Resume A")
        await _create_master(client, auth_headers, title="Resume B")

        resp = await client.get("/resumes/master", headers=auth_headers)
        assert resp.status_code == 200
        resumes = resp.json()
        assert len(resumes) == 2
        titles = {r["title"] for r in resumes}
        assert titles == {"Resume A", "Resume B"}

    async def test_list_master_resumes_scoped_to_user(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Another user's resumes must NOT appear."""
        # Create a second user directly in DB
        other = User(
            email="other@example.com",
            hashed_password=hash_password("OtherPass1!"),
            full_name="Other User",
        )
        db_session.add(other)
        await db_session.commit()
        await db_session.refresh(other)

        # Create a resume for the other user
        db_session.add(
            MasterResume(user_id=other.id, title="Other's Resume", content="...")
        )
        await db_session.commit()

        # Current user should see nothing
        resp = await client.get("/resumes/master", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    async def test_get_master_resume(
        self, client: AsyncClient, auth_headers: dict
    ):
        created = await _create_master(client, auth_headers)
        rid = created["id"]

        resp = await client.get(f"/resumes/master/{rid}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == rid

    async def test_get_master_resume_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/resumes/master/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    async def test_get_other_users_resume(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """User A must not access User B's resume."""
        other = User(
            email="sneaky@example.com",
            hashed_password=hash_password("Sneaky123!"),
            full_name="Sneaky User",
        )
        db_session.add(other)
        await db_session.commit()
        await db_session.refresh(other)

        resume = MasterResume(user_id=other.id, title="Secret", content="private stuff")
        db_session.add(resume)
        await db_session.commit()
        await db_session.refresh(resume)

        resp = await client.get(
            f"/resumes/master/{resume.id}", headers=auth_headers
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tailored Resumes
# ---------------------------------------------------------------------------


class TestTailoredResumes:
    async def test_tailor_resume(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
        db_session: AsyncSession,
    ):
        master = await _create_master(client, auth_headers)
        job = await _create_job(db_session, test_user.id)

        with patch(
            "app.agents.orchestrator.run_tailoring_pipeline",
            new=AsyncMock(return_value=_MOCK_PIPELINE_RESULT),
        ):
            resp = await client.post(
                "/resumes/tailor",
                json={
                    "master_resume_id": master["id"],
                    "job_description_id": str(job.id),
                },
                headers=auth_headers,
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["qa_status"] == "pass"
        assert data["master_resume_id"] == master["id"]
        assert data["job_description_id"] == str(job.id)
        assert data["user_id"] == str(test_user.id)

    async def test_tailor_resume_invalid_master(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
        db_session: AsyncSession,
    ):
        job = await _create_job(db_session, test_user.id)
        resp = await client.post(
            "/resumes/tailor",
            json={
                "master_resume_id": str(uuid.uuid4()),
                "job_description_id": str(job.id),
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_list_tailored_resumes(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
        db_session: AsyncSession,
    ):
        master = await _create_master(client, auth_headers)
        job = await _create_job(db_session, test_user.id)

        with patch(
            "app.agents.orchestrator.run_tailoring_pipeline",
            new=AsyncMock(return_value=_MOCK_PIPELINE_RESULT),
        ):
            await client.post(
                "/resumes/tailor",
                json={
                    "master_resume_id": master["id"],
                    "job_description_id": str(job.id),
                },
                headers=auth_headers,
            )

        resp = await client.get("/resumes/tailored", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_get_tailored_resume_with_qa(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
        db_session: AsyncSession,
    ):
        master = await _create_master(client, auth_headers)
        job = await _create_job(db_session, test_user.id)

        with patch(
            "app.agents.orchestrator.run_tailoring_pipeline",
            new=AsyncMock(return_value=_MOCK_PIPELINE_RESULT),
        ):
            create_resp = await client.post(
                "/resumes/tailor",
                json={
                    "master_resume_id": master["id"],
                    "job_description_id": str(job.id),
                },
                headers=auth_headers,
            )
        tid = create_resp.json()["id"]

        resp = await client.get(f"/resumes/tailored/{tid}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == tid
        assert "qa_status" in data
        assert "qa_score" in data

    async def test_get_tailored_resume_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        fake_id = str(uuid.uuid4())
        resp = await client.get(
            f"/resumes/tailored/{fake_id}", headers=auth_headers
        )
        assert resp.status_code == 404
