"""Tests for the PDF rendering service (HTML generation)."""

from __future__ import annotations

import pytest

from app.services.pdf_service import _RESUME_CSS, get_resume_html


class TestGetResumeHtml:
    def test_contains_user_name(self):
        html = get_resume_html("Some resume content", "Alice Johnson")
        assert "Alice Johnson" in html
        assert "<h1>" in html

    def test_contains_resume_content(self):
        content = "## Experience\n- Built REST APIs with FastAPI"
        html = get_resume_html(content, "Test User")
        # Markdown should be converted to HTML
        assert "Experience" in html
        assert "FastAPI" in html

    def test_has_modern_classic_css(self):
        html = get_resume_html("content", "User")
        # Check for key Modern Classic CSS characteristics
        assert "font-family" in html
        assert "Georgia" in html or "Arial" in html
        assert "<style>" in html

    def test_resume_html_has_single_column_layout(self):
        """Verify the CSS doesn't use multi-column layout."""
        # The _RESUME_CSS should not contain column-count or grid layouts
        assert "column-count" not in _RESUME_CSS
        assert "display: grid" not in _RESUME_CSS
        # It IS a single-column, serif-accented resume
        assert "Georgia" in _RESUME_CSS

    def test_html_is_valid_document(self):
        html = get_resume_html("## Skills\n- Python\n- SQL", "Jane Doe")
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html
        assert "<body>" in html
        assert "</body>" in html

    def test_html_escapes_user_name(self):
        """XSS protection: special characters in user_name should be escaped."""
        html = get_resume_html("content", '<script>alert("xss")</script>')
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_css_ats_friendly_font_sizes(self):
        """ATS scanners work best with standard font sizes."""
        assert "10.5pt" in _RESUME_CSS  # body font size
        assert "22pt" in _RESUME_CSS  # h1 font size

    def test_page_size_is_letter(self):
        assert "Letter" in _RESUME_CSS
