"""Tests for job description endpoints (POST /jobs, GET /jobs, GET /jobs/{id})."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.models.user import User


class TestCreateJob:
    async def test_create_job_from_text(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        resp = await client.post(
            "/jobs/",
            data={
                "raw_text": "We are looking for a Python engineer with 5+ years experience.",
                "company_name": "TestCorp",
                "job_title": "Python Engineer",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["raw_text"].startswith("We are looking")
        assert data["company_name"] == "TestCorp"
        assert data["job_title"] == "Python Engineer"
        assert data["user_id"] == str(test_user.id)

    async def test_create_job_from_url(
        self, client: AsyncClient, auth_headers: dict
    ):
        resp = await client.post(
            "/jobs/",
            data={
                "source_url": "https://example.com/jobs/123",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "example.com" in data["raw_text"]
        assert data["source_url"] == "https://example.com/jobs/123"

    async def test_create_job_no_input(
        self, client: AsyncClient, auth_headers: dict
    ):
        resp = await client.post(
            "/jobs/",
            data={},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "provide" in resp.json()["detail"].lower()


class TestListJobs:
    async def test_list_jobs(
        self, client: AsyncClient, auth_headers: dict
    ):
        # Create two jobs
        for i in range(2):
            await client.post(
                "/jobs/",
                data={"raw_text": f"Job description #{i}"},
                headers=auth_headers,
            )

        resp = await client.get("/jobs/", headers=auth_headers)
        assert resp.status_code == 200
        jobs = resp.json()
        assert len(jobs) == 2

    async def test_list_jobs_empty(
        self, client: AsyncClient, auth_headers: dict
    ):
        resp = await client.get("/jobs/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetJob:
    async def test_get_job(
        self, client: AsyncClient, auth_headers: dict
    ):
        create_resp = await client.post(
            "/jobs/",
            data={"raw_text": "Full stack developer needed", "job_title": "Full Stack Dev"},
            headers=auth_headers,
        )
        job_id = create_resp.json()["id"]

        resp = await client.get(f"/jobs/{job_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == job_id
        assert resp.json()["job_title"] == "Full Stack Dev"

    async def test_get_job_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/jobs/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404
