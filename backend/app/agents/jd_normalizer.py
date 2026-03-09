"""JD Normalizer Agent — extracts structured JSON from raw job descriptions."""

from __future__ import annotations

import json
import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from app.agents.prompts import JD_NORMALIZER_PROMPT
from app.config import settings

logger = logging.getLogger(__name__)

_llm: ChatOllama | None = None


def _get_llm() -> ChatOllama:
    global _llm
    if _llm is None:
        _llm = ChatOllama(
            model="llama3",
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.0,
        )
    return _llm


_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", JD_NORMALIZER_PROMPT),
        ("human", "Job Description:\n\n{raw_text}"),
    ]
)


def _parse_json_response(text: str) -> dict:
    """Extract JSON from LLM output, handling possible markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Strip ```json ... ``` wrappers
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)


async def normalize_jd(raw_text: str) -> dict:
    """Take raw job description text and return structured JSON.

    Returns a dict with keys: job_title, core_skills, soft_skills,
    metrics_expected, company_culture_keywords.
    """
    llm = _get_llm()
    chain = _prompt | llm | StrOutputParser()

    logger.info("Normalizing job description (%d chars)", len(raw_text))
    response = await chain.ainvoke({"raw_text": raw_text})

    try:
        result = _parse_json_response(response)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("First parse failed, retrying with stricter prompt: %s", exc)
        retry_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", JD_NORMALIZER_PROMPT),
                (
                    "human",
                    "Your previous response was not valid JSON. "
                    "Please try again. Output ONLY valid JSON.\n\n"
                    "Job Description:\n\n{raw_text}",
                ),
            ]
        )
        retry_chain = retry_prompt | llm | StrOutputParser()
        response = await retry_chain.ainvoke({"raw_text": raw_text})
        result = _parse_json_response(response)

    expected_keys = {
        "job_title",
        "core_skills",
        "soft_skills",
        "metrics_expected",
        "company_culture_keywords",
    }
    for key in expected_keys:
        result.setdefault(key, [] if key != "job_title" else "Unknown")

    logger.info("JD normalized: title=%s, %d core skills", result["job_title"], len(result["core_skills"]))
    return result
