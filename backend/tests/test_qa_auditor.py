"""Tests for the QA auditor's deterministic programmatic_diff function."""

from __future__ import annotations

import pytest

from app.agents.qa_auditor import programmatic_diff


class TestProgrammaticDiff:
    def test_no_new_skills(self):
        master = ["Python", "FastAPI", "Docker"]
        draft = ["Python", "FastAPI"]
        result = programmatic_diff(master, draft)
        assert result == []

    def test_detects_new_skills(self):
        master = ["Python", "FastAPI"]
        draft = ["Python", "FastAPI", "Kubernetes", "Go"]
        result = programmatic_diff(master, draft)
        assert set(result) == {"Kubernetes", "Go"}

    def test_case_insensitive(self):
        master = ["python", "FASTAPI", "Docker"]
        draft = ["Python", "fastapi", "docker"]
        result = programmatic_diff(master, draft)
        assert result == []

    def test_empty_master(self):
        result = programmatic_diff([], ["Python", "Go"])
        assert set(result) == {"Python", "Go"}

    def test_empty_draft(self):
        result = programmatic_diff(["Python", "Go"], [])
        assert result == []

    def test_both_empty(self):
        result = programmatic_diff([], [])
        assert result == []

    def test_whitespace_handling(self):
        master = ["  Python  ", "FastAPI"]
        draft = ["Python", "FastAPI  "]
        result = programmatic_diff(master, draft)
        assert result == []

    def test_returns_list_preserving_draft_order(self):
        master = ["A"]
        draft = ["A", "C", "B"]
        result = programmatic_diff(master, draft)
        assert result == ["C", "B"]
