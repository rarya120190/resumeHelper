"""QA Auditor Agent — validates tailored drafts against the master resume."""

from __future__ import annotations

import json
import logging

from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate

from app.agents.prompts import QA_AUDITOR_PROMPT
from app.config import settings

logger = logging.getLogger(__name__)

_llm: Ollama | None = None


def _get_llm() -> Ollama:
    global _llm
    if _llm is None:
        _llm = Ollama(
            model="llama3",
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.0,
        )
    return _llm


_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", QA_AUDITOR_PROMPT),
        (
            "human",
            "## Master Resume\n{master_resume}\n\n"
            "## Tailored Draft\n{tailored_draft}\n\n"
            "Audit the draft now.",
        ),
    ]
)


def _parse_json_response(text: str) -> dict:
    """Extract JSON from LLM output, handling possible markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)


def programmatic_diff(
    master_skills: list[str], draft_skills: list[str]
) -> list[str]:
    """Deterministic check: return skills in the draft that are not in the master.

    Comparison is case-insensitive and strips whitespace.
    """
    master_normalised = {s.strip().lower() for s in master_skills}
    new_skills = [
        s for s in draft_skills if s.strip().lower() not in master_normalised
    ]
    return new_skills


async def audit_resume(master_resume: str, tailored_draft: str) -> dict:
    """Audit a tailored resume against the master.

    Returns:
        dict with keys:
        - status: "PASS" or "FAIL"
        - violations: list[str]
        - confidence_score: int (0-100)
    """
    llm = _get_llm()
    chain = _prompt | llm

    logger.info("Running QA audit on tailored draft (%d chars)", len(tailored_draft))
    response = await chain.ainvoke(
        {"master_resume": master_resume, "tailored_draft": tailored_draft}
    )

    try:
        result = _parse_json_response(response)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("QA audit parse failed, retrying: %s", exc)
        retry_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", QA_AUDITOR_PROMPT),
                (
                    "human",
                    "Your previous response was not valid JSON. "
                    "Please output ONLY valid JSON.\n\n"
                    "## Master Resume\n{master_resume}\n\n"
                    "## Tailored Draft\n{tailored_draft}",
                ),
            ]
        )
        retry_chain = retry_prompt | llm
        response = await retry_chain.ainvoke(
            {"master_resume": master_resume, "tailored_draft": tailored_draft}
        )
        result = _parse_json_response(response)

    # Normalise result shape
    result.setdefault("status", "FAIL")
    result.setdefault("violations", [])
    result.setdefault("confidence_score", 0)

    # Coerce types
    if isinstance(result["confidence_score"], str):
        try:
            result["confidence_score"] = int(result["confidence_score"])
        except ValueError:
            result["confidence_score"] = 0

    result["confidence_score"] = max(0, min(100, result["confidence_score"]))

    if result["violations"] and result["status"] != "FAIL":
        result["status"] = "FAIL"

    logger.info(
        "QA audit complete: status=%s, confidence=%d, violations=%d",
        result["status"],
        result["confidence_score"],
        len(result["violations"]),
    )
    return result
