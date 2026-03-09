"""Company Enrichment Agent — produces a Context Brief for a target company."""

from __future__ import annotations

import json
import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from app.agents.prompts import COMPANY_ENRICHMENT_PROMPT
from app.config import settings

logger = logging.getLogger(__name__)

_llm: ChatOllama | None = None


def _get_llm() -> ChatOllama:
    global _llm
    if _llm is None:
        _llm = ChatOllama(
            model="llama3",
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.2,
        )
    return _llm


_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", COMPANY_ENRICHMENT_PROMPT),
        (
            "human",
            "Company Name: {company_name}\n"
            "Company URL: {company_url}\n\n"
            "Produce the Context Brief.",
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


async def enrich_company(company_name: str, company_url: str | None = None) -> dict:
    """Return a Context Brief JSON for the given company.

    Returns a dict with keys: company_summary, pain_points,
    engineering_team_tone, power_keywords.
    """
    llm = _get_llm()
    chain = _prompt | llm | StrOutputParser()

    url_str = company_url or "Not provided"
    logger.info("Enriching company: %s (url=%s)", company_name, url_str)
    response = await chain.ainvoke(
        {"company_name": company_name, "company_url": url_str}
    )

    try:
        result = _parse_json_response(response)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("First parse failed, retrying: %s", exc)
        retry_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", COMPANY_ENRICHMENT_PROMPT),
                (
                    "human",
                    "Your previous response was not valid JSON. "
                    "Please try again. Output ONLY valid JSON.\n\n"
                    "Company Name: {company_name}\n"
                    "Company URL: {company_url}",
                ),
            ]
        )
        retry_chain = retry_prompt | llm | StrOutputParser()
        response = await retry_chain.ainvoke(
            {"company_name": company_name, "company_url": url_str}
        )
        result = _parse_json_response(response)

    result.setdefault("company_summary", "")
    result.setdefault("pain_points", [])
    result.setdefault("engineering_team_tone", "unknown")
    result.setdefault("power_keywords", [])

    logger.info(
        "Company enrichment complete: %s — %d power keywords",
        company_name,
        len(result["power_keywords"]),
    )
    return result
