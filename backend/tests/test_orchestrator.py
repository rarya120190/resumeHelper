"""Tests for the pipeline orchestrator (LangGraph workflow)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Mock helper: simulate a full pipeline execution
# ---------------------------------------------------------------------------

def _mock_normalize_jd():
    """Return a mock for normalize_jd."""
    return AsyncMock(
        return_value={
            "job_title": "Senior Python Developer",
            "core_skills": ["Python", "FastAPI", "PostgreSQL"],
            "soft_skills": ["Leadership"],
            "metrics_expected": [],
            "company_culture_keywords": ["innovative"],
        }
    )


def _mock_enrich_company():
    return AsyncMock(
        return_value={
            "company_summary": "Acme is a tech company.",
            "pain_points": ["Scaling"],
            "engineering_team_tone": "startup-casual",
            "power_keywords": ["scalable", "cloud-native", "data-driven"],
        }
    )


def _mock_write_resume(content: str = "Tailored resume content goes here."):
    return AsyncMock(return_value=content)


def _mock_audit_pass():
    return AsyncMock(
        return_value={
            "status": "PASS",
            "violations": [],
            "confidence_score": 95,
        }
    )


def _mock_audit_fail():
    return AsyncMock(
        return_value={
            "status": "FAIL",
            "violations": ["New skill 'Go' not in master"],
            "confidence_score": 40,
        }
    )


def _mock_mask_pii():
    return MagicMock(
        side_effect=lambda text: (text, {})
    )


def _mock_rehydrate_pii():
    return MagicMock(side_effect=lambda text, mapping: text)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestOrchestrator:
    @patch("app.agents.orchestrator.audit_resume")
    @patch("app.agents.orchestrator.write_tailored_resume")
    @patch("app.agents.orchestrator.enrich_company")
    @patch("app.agents.orchestrator.normalize_jd")
    @patch("app.agents.orchestrator._rehydrate_resume")
    @patch("app.agents.orchestrator._mask_resume")
    async def test_full_pipeline_success(
        self,
        mock_mask,
        mock_rehydrate,
        mock_normalize,
        mock_enrich,
        mock_write,
        mock_audit,
    ):
        mock_mask.side_effect = lambda text: (text, {})
        mock_rehydrate.side_effect = lambda text, mapping: text
        mock_normalize.return_value = {
            "job_title": "Python Dev",
            "core_skills": ["Python"],
            "soft_skills": [],
            "metrics_expected": [],
            "company_culture_keywords": [],
        }
        mock_enrich.return_value = {
            "company_summary": "Tech co",
            "pain_points": [],
            "engineering_team_tone": "formal",
            "power_keywords": ["cloud"],
        }
        mock_write.return_value = "Tailored resume output"
        mock_audit.return_value = {
            "status": "PASS",
            "violations": [],
            "confidence_score": 92,
        }

        # Re-compile the graph to pick up mocked functions
        from app.agents.orchestrator import run_tailoring_pipeline

        result = await run_tailoring_pipeline(
            master_resume="John Smith - Python developer with 5 years experience.",
            jd_text="Looking for Python dev with FastAPI experience.",
            company_name="TestCorp",
        )

        assert result["final_draft"] != ""
        assert result["qa_passed"] is True
        assert result["confidence_score"] >= 90

    @patch("app.agents.orchestrator.audit_resume")
    @patch("app.agents.orchestrator.write_tailored_resume")
    @patch("app.agents.orchestrator.enrich_company")
    @patch("app.agents.orchestrator.normalize_jd")
    @patch("app.agents.orchestrator._rehydrate_resume")
    @patch("app.agents.orchestrator._mask_resume")
    async def test_pipeline_retries_on_qa_fail(
        self,
        mock_mask,
        mock_rehydrate,
        mock_normalize,
        mock_enrich,
        mock_write,
        mock_audit,
    ):
        mock_mask.side_effect = lambda text: (text, {})
        mock_rehydrate.side_effect = lambda text, mapping: text
        mock_normalize.return_value = {
            "job_title": "Dev",
            "core_skills": ["Python"],
            "soft_skills": [],
            "metrics_expected": [],
            "company_culture_keywords": [],
        }
        mock_enrich.return_value = None
        mock_write.return_value = "Improved resume"

        # First call FAILs, second call PASSes
        mock_audit.side_effect = [
            {
                "status": "FAIL",
                "violations": ["Added skill 'Go'"],
                "confidence_score": 40,
            },
            {
                "status": "PASS",
                "violations": [],
                "confidence_score": 88,
            },
        ]

        from app.agents.orchestrator import run_tailoring_pipeline

        result = await run_tailoring_pipeline(
            master_resume="My resume text",
            jd_text="Job description text",
        )

        assert result["qa_passed"] is True
        assert result["retry_count"] >= 1

    @patch("app.agents.orchestrator.audit_resume")
    @patch("app.agents.orchestrator.write_tailored_resume")
    @patch("app.agents.orchestrator.enrich_company")
    @patch("app.agents.orchestrator.normalize_jd")
    @patch("app.agents.orchestrator._rehydrate_resume")
    @patch("app.agents.orchestrator._mask_resume")
    async def test_pipeline_max_retries_exceeded(
        self,
        mock_mask,
        mock_rehydrate,
        mock_normalize,
        mock_enrich,
        mock_write,
        mock_audit,
    ):
        mock_mask.side_effect = lambda text: (text, {})
        mock_rehydrate.side_effect = lambda text, mapping: text
        mock_normalize.return_value = {
            "job_title": "Dev",
            "core_skills": [],
            "soft_skills": [],
            "metrics_expected": [],
            "company_culture_keywords": [],
        }
        mock_enrich.return_value = None
        mock_write.return_value = "Bad resume"

        # Always fail
        mock_audit.return_value = {
            "status": "FAIL",
            "violations": ["Hallucinated skill"],
            "confidence_score": 20,
        }

        from app.agents.orchestrator import run_tailoring_pipeline, MAX_RETRIES

        result = await run_tailoring_pipeline(
            master_resume="Resume",
            jd_text="JD",
        )

        # Should have given up after MAX_RETRIES
        assert result["qa_passed"] is False
        assert result["retry_count"] <= MAX_RETRIES + 1

    @patch("app.agents.orchestrator.normalize_jd")
    async def test_pipeline_handles_exception(self, mock_normalize):
        """If an agent raises, the pipeline returns an error dict."""
        mock_normalize.side_effect = RuntimeError("LLM service unavailable")

        from app.agents.orchestrator import run_tailoring_pipeline

        result = await run_tailoring_pipeline(
            master_resume="Resume",
            jd_text="JD",
        )

        assert result["error"] is not None
        assert "unavailable" in result["error"].lower()
        assert result["qa_passed"] is False
