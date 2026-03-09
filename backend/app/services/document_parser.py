from __future__ import annotations

import io
import os


def parse_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file.

    Parameters
    ----------
    file_bytes : bytes
        Raw bytes of the PDF document.

    Returns
    -------
    str
        Extracted text with pages separated by newlines.

    Raises
    ------
    ValueError
        If the PDF contains no extractable text.
    """
    import pdfplumber

    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)

    if not pages:
        raise ValueError("PDF contains no extractable text")
    return "\n\n".join(pages)


def parse_docx(file_bytes: bytes) -> str:
    """Extract text from a Word (.docx) file.

    Parameters
    ----------
    file_bytes : bytes
        Raw bytes of the DOCX document.

    Returns
    -------
    str
        Extracted text with paragraphs separated by newlines.

    Raises
    ------
    ValueError
        If the document contains no text.
    """
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

    if not paragraphs:
        raise ValueError("DOCX document contains no text")
    return "\n\n".join(paragraphs)


def parse_document(file_bytes: bytes, filename: str) -> str:
    """Route to the correct parser based on the file extension.

    Parameters
    ----------
    file_bytes : bytes
        Raw file content.
    filename : str
        Original filename (used to determine the format).

    Returns
    -------
    str
        Extracted text.

    Raises
    ------
    ValueError
        If the file type is unsupported.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        return parse_pdf(file_bytes)
    if ext in (".docx",):
        return parse_docx(file_bytes)
    if ext == ".txt":
        return file_bytes.decode("utf-8")

    raise ValueError(f"Unsupported file type: {ext!r}. Accepted: .pdf, .docx, .txt")
