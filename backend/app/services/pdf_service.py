from __future__ import annotations

import html
import re

import markdown as md  # type: ignore[import-untyped]
from weasyprint import HTML  # type: ignore[import-untyped]

# ── "Modern Classic" ATS-friendly stylesheet ────────────────────────────
_RESUME_CSS = """\
/* Reset */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

@page {
    size: Letter;
    margin: 0.75in 0.85in;
}

body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 10.5pt;
    line-height: 1.45;
    color: #222;
    -webkit-font-smoothing: antialiased;
}

/* ── Header / Name ─────────────────────────────────────────────── */
h1 {
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 22pt;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 2pt;
    border-bottom: 2px solid #333;
    padding-bottom: 6pt;
}

/* ── Section headers ───────────────────────────────────────────── */
h2 {
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 13pt;
    font-weight: 700;
    color: #1a1a1a;
    text-transform: uppercase;
    letter-spacing: 0.5pt;
    margin-top: 14pt;
    margin-bottom: 4pt;
    border-bottom: 1px solid #999;
    padding-bottom: 2pt;
}

/* ── Sub-headers (job title / degree) ──────────────────────────── */
h3 {
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 11pt;
    font-weight: 700;
    color: #333;
    margin-top: 8pt;
    margin-bottom: 1pt;
}

h4, h5, h6 {
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 10.5pt;
    font-weight: 600;
    color: #444;
    margin-top: 4pt;
    margin-bottom: 1pt;
}

/* ── Paragraphs ────────────────────────────────────────────────── */
p {
    margin-bottom: 4pt;
}

/* ── Lists (bullet points) ─────────────────────────────────────── */
ul, ol {
    margin-left: 16pt;
    margin-bottom: 4pt;
}

li {
    margin-bottom: 2pt;
}

/* ── Links ─────────────────────────────────────────────────────── */
a {
    color: #1a0dab;
    text-decoration: none;
}

/* ── Bold / Italic ─────────────────────────────────────────────── */
strong { font-weight: 700; }
em     { font-style: italic; }

/* ── Horizontal rules ──────────────────────────────────────────── */
hr {
    border: none;
    border-top: 1px solid #ccc;
    margin: 10pt 0;
}

/* ── Contact info line (first paragraph after h1) ──────────────── */
.contact-info {
    font-size: 9.5pt;
    color: #555;
    margin-bottom: 8pt;
}
"""

# ── Helpers ─────────────────────────────────────────────────────────────

def _markdown_to_html(text: str) -> str:
    """Convert markdown/plain text to HTML body content."""
    return md.markdown(
        text,
        extensions=["extra", "sane_lists", "smarty"],
        output_format="html",
    )


def get_resume_html(resume_content: str, user_name: str) -> str:
    """Build a complete HTML document for the resume.

    Parameters
    ----------
    resume_content : str
        Resume body in Markdown or plain text.
    user_name : str
        Candidate's full name, rendered as the ``<h1>`` header.

    Returns
    -------
    str
        Fully-formed HTML string with embedded CSS ready for PDF conversion.
    """
    safe_name = html.escape(user_name)
    body_html = _markdown_to_html(resume_content)

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        f"  <title>{safe_name} — Resume</title>\n"
        f"  <style>{_RESUME_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        f"  <h1>{safe_name}</h1>\n"
        f"  {body_html}\n"
        "</body>\n"
        "</html>"
    )


def render_resume_pdf(resume_content: str, user_name: str) -> bytes:
    """Render a styled PDF resume.

    Parameters
    ----------
    resume_content : str
        Resume body in Markdown or plain text.
    user_name : str
        Candidate's full name, placed at the top of the document.

    Returns
    -------
    bytes
        PDF file contents.
    """
    html_string = get_resume_html(resume_content, user_name)
    return HTML(string=html_string).write_pdf()
