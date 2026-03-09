"""Tests for the PII masking / rehydration service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# We mock the Presidio engines at the module level so tests run without
# the spaCy model or Presidio installed.
# ---------------------------------------------------------------------------

def _build_mock_analyzer():
    """Return a mock analyzer that recognises names, emails, and phones."""
    from types import SimpleNamespace

    def _analyze(text: str, language: str, entities: list[str]):
        results = []
        # Simple pattern-based mock detection
        import re

        # Emails
        for m in re.finditer(r"[\w.+-]+@[\w-]+\.[\w.]+", text):
            results.append(
                SimpleNamespace(
                    entity_type="EMAIL_ADDRESS",
                    start=m.start(),
                    end=m.end(),
                    score=0.99,
                )
            )
        # Phones  (xxx-xxx-xxxx)
        for m in re.finditer(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", text):
            results.append(
                SimpleNamespace(
                    entity_type="PHONE_NUMBER",
                    start=m.start(),
                    end=m.end(),
                    score=0.9,
                )
            )
        # Names — anything wrapped in double-curly brackets is a cheat marker
        # For realistic tests, detect well-known patterns like "John Smith"
        known_names = ["John Smith", "Jane Doe", "Alice Johnson"]
        for name in known_names:
            idx = text.find(name)
            while idx != -1:
                results.append(
                    SimpleNamespace(
                        entity_type="PERSON",
                        start=idx,
                        end=idx + len(name),
                        score=0.95,
                    )
                )
                idx = text.find(name, idx + 1)

        return results

    mock = MagicMock()
    mock.analyze = _analyze
    return mock


@pytest.fixture(autouse=True)
def _mock_presidio(monkeypatch):
    """Replace the PII service's global analyzer with our simple mock."""
    import app.services.pii_service as mod

    monkeypatch.setattr(mod, "_analyzer", _build_mock_analyzer())
    # No need to mock the anonymizer because the service does replacement manually


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

from app.services.pii_service import mask_pii, rehydrate_pii


class TestMaskPII:
    def test_mask_pii_names(self):
        text = "My name is John Smith and I work at Acme."
        masked, token_map = mask_pii(text)
        assert "John Smith" not in masked
        assert "<PERSON_1>" in masked
        assert token_map["<PERSON_1>"] == "John Smith"

    def test_mask_pii_emails(self):
        text = "Contact me at john@example.com for details."
        masked, token_map = mask_pii(text)
        assert "john@example.com" not in masked
        assert "<EMAIL_1>" in masked
        assert token_map["<EMAIL_1>"] == "john@example.com"

    def test_mask_pii_phones(self):
        text = "Call me at 555-123-4567."
        masked, token_map = mask_pii(text)
        assert "555-123-4567" not in masked
        assert "<PHONE_1>" in masked
        assert token_map["<PHONE_1>"] == "555-123-4567"

    def test_mask_pii_multiple_entities(self):
        text = "John Smith (john@example.com, 555-123-4567) is a developer."
        masked, token_map = mask_pii(text)
        assert "John Smith" not in masked
        assert "john@example.com" not in masked
        assert "555-123-4567" not in masked
        assert len(token_map) == 3

    def test_no_pii_passthrough(self):
        text = "This text has no personally identifiable information."
        masked, token_map = mask_pii(text)
        assert masked == text
        assert token_map == {}

    def test_empty_text_handling(self):
        masked, token_map = mask_pii("")
        assert masked == ""
        assert token_map == {}


class TestRehydratePII:
    def test_rehydrate_restores_original(self):
        original = "John Smith can be reached at john@example.com or 555-123-4567."
        masked, token_map = mask_pii(original)
        restored = rehydrate_pii(masked, token_map)
        assert restored == original

    def test_rehydrate_preserves_structure(self):
        text = "Name: John Smith\nEmail: john@example.com\nPhone: 555-123-4567"
        masked, token_map = mask_pii(text)
        restored = rehydrate_pii(masked, token_map)
        assert restored == text
        # Verify newlines are preserved
        assert restored.count("\n") == text.count("\n")

    def test_rehydrate_empty_map(self):
        text = "Nothing to see here."
        assert rehydrate_pii(text, {}) == text

    def test_rehydrate_with_multiple_same_entity(self):
        text = "John Smith and John Smith again."
        masked, token_map = mask_pii(text)
        restored = rehydrate_pii(masked, token_map)
        assert restored == text
