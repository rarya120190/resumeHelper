"""Tests for the document parser (PDF, DOCX, TXT routing)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.document_parser import parse_document, parse_docx, parse_pdf


class TestParsePdf:
    @patch("app.services.document_parser.pdfplumber")
    def test_parse_pdf_returns_text(self, mock_pdfplumber):
        """Mock pdfplumber to return two pages of text."""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(b"fake-pdf-bytes")
        assert "Page 1 content" in result
        assert "Page 2 content" in result

    @patch("app.services.document_parser.pdfplumber")
    def test_parse_pdf_empty_raises(self, mock_pdfplumber):
        """PDF with no extractable text should raise ValueError."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdfplumber.open.return_value = mock_pdf

        with pytest.raises(ValueError, match="no extractable text"):
            parse_pdf(b"fake-pdf-bytes")


class TestParseDocx:
    @patch("app.services.document_parser.Document")
    def test_parse_docx_returns_text(self, mock_document_cls):
        para1 = MagicMock()
        para1.text = "Summary paragraph"
        para2 = MagicMock()
        para2.text = "Experience paragraph"
        para_empty = MagicMock()
        para_empty.text = "  "  # whitespace-only → should be skipped

        mock_doc = MagicMock()
        mock_doc.paragraphs = [para1, para_empty, para2]
        mock_document_cls.return_value = mock_doc

        result = parse_docx(b"fake-docx-bytes")
        assert "Summary paragraph" in result
        assert "Experience paragraph" in result

    @patch("app.services.document_parser.Document")
    def test_parse_docx_empty_raises(self, mock_document_cls):
        mock_doc = MagicMock()
        mock_doc.paragraphs = []
        mock_document_cls.return_value = mock_doc

        with pytest.raises(ValueError, match="no text"):
            parse_docx(b"fake-docx-bytes")


class TestParseDocument:
    @patch("app.services.document_parser.parse_pdf")
    def test_routes_pdf(self, mock_parse_pdf):
        mock_parse_pdf.return_value = "pdf text"
        result = parse_document(b"bytes", "resume.pdf")
        assert result == "pdf text"
        mock_parse_pdf.assert_called_once_with(b"bytes")

    @patch("app.services.document_parser.parse_docx")
    def test_routes_docx(self, mock_parse_docx):
        mock_parse_docx.return_value = "docx text"
        result = parse_document(b"bytes", "resume.docx")
        assert result == "docx text"
        mock_parse_docx.assert_called_once_with(b"bytes")

    def test_routes_txt(self):
        content = "Plain text resume content."
        result = parse_document(content.encode("utf-8"), "resume.txt")
        assert result == content

    def test_unsupported_format_raises_error(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            parse_document(b"bytes", "resume.jpg")

    def test_unsupported_format_xlsx(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            parse_document(b"bytes", "data.xlsx")
