"""Tests for individual AI agents with mocked LLM calls."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# JD Normalizer
# ---------------------------------------------------------------------------


class TestJDNormalizer:
    @patch("app.agents.jd_normalizer._get_llm")
    async def test_jd_normalizer_returns_structured_json(self, mock_get_llm):
        expected = {
            "job_title": "Senior Python Developer",
            "core_skills": ["Python", "FastAPI", "PostgreSQL"],
            "soft_skills": ["Communication", "Leadership"],
            "metrics_expected": ["Reduce latency by 30%"],
            "company_culture_keywords": ["innovative", "agile"],
        }

        mock_llm = MagicMock()
        mock_llm.__or__ = MagicMock(
            side_effect=lambda other: other  # passthrough for pipe
        )
        # Make the chain's ainvoke return our JSON string
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value=json.dumps(expected))

        mock_get_llm.return_value = mock_llm

        with patch("app.agents.jd_normalizer._prompt") as mock_prompt:
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)

            from app.agents.jd_normalizer import normalize_jd

            result = await normalize_jd("We are looking for a Senior Python Developer...")

        assert result["job_title"] == "Senior Python Developer"
        assert "Python" in result["core_skills"]
        assert isinstance(result["soft_skills"], list)

    @patch("app.agents.jd_normalizer._get_llm")
    async def test_jd_normalizer_handles_markdown_fencing(self, mock_get_llm):
        """LLM may wrap JSON in ```json ... ``` fences."""
        expected = {"job_title": "Data Engineer", "core_skills": ["Spark"]}
        fenced_response = f"```json\n{json.dumps(expected)}\n```"

        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value=fenced_response)

        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        with patch("app.agents.jd_normalizer._prompt") as mock_prompt:
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)

            from app.agents.jd_normalizer import normalize_jd

            result = await normalize_jd("Data engineer needed")

        assert result["job_title"] == "Data Engineer"


# ---------------------------------------------------------------------------
# Company Enrichment
# ---------------------------------------------------------------------------


class TestCompanyEnrichment:
    @patch("app.agents.company_enrichment._get_llm")
    async def test_returns_context_brief(self, mock_get_llm):
        expected = {
            "company_summary": "Acme Corp is an innovative tech company.",
            "pain_points": ["Scaling infrastructure", "Talent retention"],
            "engineering_team_tone": "startup-casual",
            "power_keywords": ["scalable", "cloud-native", "data-driven"],
        }

        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value=json.dumps(expected))

        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        with patch("app.agents.company_enrichment._prompt") as mock_prompt:
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)

            from app.agents.company_enrichment import enrich_company

            result = await enrich_company("Acme Corp", "https://acme.com")

        assert "Acme Corp" in result["company_summary"]
        assert len(result["power_keywords"]) == 3
        assert isinstance(result["pain_points"], list)

    @patch("app.agents.company_enrichment._get_llm")
    async def test_enrichment_defaults_missing_keys(self, mock_get_llm):
        """Service should fill in defaults for missing keys."""
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value='{"company_summary": "A company."}')

        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        with patch("app.agents.company_enrichment._prompt") as mock_prompt:
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)

            from app.agents.company_enrichment import enrich_company

            result = await enrich_company("Unknown Inc")

        assert "pain_points" in result
        assert "power_keywords" in result


# ---------------------------------------------------------------------------
# Resume Writer
# ---------------------------------------------------------------------------


class TestResumeWriter:
    @patch("app.agents.resume_writer.settings")
    async def test_uses_openai_when_available(self, mock_settings):
        mock_settings.OPENAI_API_KEY = "sk-test-key"
        mock_settings.ANTHROPIC_API_KEY = ""

        mock_response = MagicMock()
        mock_response.content = "# Tailored Resume\n## Experience\n- Built APIs"

        with patch("app.agents.resume_writer._llm", None):
            with patch("app.agents.resume_writer.ChatOpenAI") as MockOpenAI:
                mock_instance = MagicMock()
                MockOpenAI.return_value = mock_instance

                mock_chain = AsyncMock()
                mock_chain.ainvoke = AsyncMock(return_value=mock_response)

                with patch("app.agents.resume_writer._prompt") as mock_prompt:
                    mock_prompt.__or__ = MagicMock(return_value=mock_chain)

                    from app.agents.resume_writer import _get_llm

                    # Reset the cached LLM
                    import app.agents.resume_writer as rw_mod
                    rw_mod._llm = None

                    llm = _get_llm()
                    MockOpenAI.assert_called_once()

                    # Clean up
                    rw_mod._llm = None

    @patch("app.agents.resume_writer.settings")
    async def test_falls_back_to_anthropic(self, mock_settings):
        mock_settings.OPENAI_API_KEY = ""
        mock_settings.ANTHROPIC_API_KEY = "sk-ant-test-key"

        with patch("app.agents.resume_writer._llm", None):
            with patch("app.agents.resume_writer.ChatAnthropic") as MockAnthropic:
                mock_instance = MagicMock()
                MockAnthropic.return_value = mock_instance

                import app.agents.resume_writer as rw_mod
                rw_mod._llm = None

                llm = rw_mod._get_llm()
                MockAnthropic.assert_called_once()

                rw_mod._llm = None

    @patch("app.agents.resume_writer.settings")
    async def test_raises_when_no_keys(self, mock_settings):
        mock_settings.OPENAI_API_KEY = ""
        mock_settings.ANTHROPIC_API_KEY = ""

        import app.agents.resume_writer as rw_mod
        rw_mod._llm = None

        with pytest.raises(RuntimeError, match="No premium AI key"):
            rw_mod._get_llm()

        rw_mod._llm = None


# ---------------------------------------------------------------------------
# QA Auditor (LLM-backed audit)
# ---------------------------------------------------------------------------


class TestQAAuditorLLM:
    @patch("app.agents.qa_auditor._get_llm")
    async def test_returns_pass_fail_result(self, mock_get_llm):
        expected = {
            "status": "PASS",
            "violations": [],
            "confidence_score": 95,
        }

        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value=json.dumps(expected))

        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        with patch("app.agents.qa_auditor._prompt") as mock_prompt:
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)

            from app.agents.qa_auditor import audit_resume

            result = await audit_resume("master text", "draft text")

        assert result["status"] == "PASS"
        assert result["confidence_score"] == 95
        assert result["violations"] == []

    @patch("app.agents.qa_auditor._get_llm")
    async def test_returns_fail_with_violations(self, mock_get_llm):
        expected = {
            "status": "FAIL",
            "violations": ["New skill 'Kubernetes' not in master"],
            "confidence_score": 40,
        }

        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value=json.dumps(expected))

        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        with patch("app.agents.qa_auditor._prompt") as mock_prompt:
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)

            from app.agents.qa_auditor import audit_resume

            result = await audit_resume("master text", "draft text")

        assert result["status"] == "FAIL"
        assert len(result["violations"]) == 1


# ---------------------------------------------------------------------------
# Rulebook Agent
# ---------------------------------------------------------------------------


class TestRulebookAgent:
    @patch("app.agents.rulebook_agent._get_llm")
    async def test_extracts_rules(self, mock_get_llm):
        expected_rules = [
            "Always use past tense for experience bullets",
            "Use MM/YYYY date format",
        ]

        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value=json.dumps(expected_rules))

        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        with patch("app.agents.rulebook_agent._prompt") as mock_prompt:
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)

            from app.agents.rulebook_agent import extract_style_rules

            rules = await extract_style_rules(
                ai_version="AI generated resume...",
                user_version="User edited resume...",
            )

        assert len(rules) == 2
        assert "past tense" in rules[0].lower()
