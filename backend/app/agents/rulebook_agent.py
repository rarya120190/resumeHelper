"""Rulebook Agent — extracts user style preferences from edit diffs."""

from __future__ import annotations

import json
import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from app.agents.prompts import RULEBOOK_UPDATER_PROMPT
from app.config import settings

logger = logging.getLogger(__name__)

_llm: ChatOllama | None = None


def _get_llm() -> ChatOllama:
    global _llm
    if _llm is None:
        _llm = ChatOllama(
            model="llama3",
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.3,
        )
    return _llm


_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", RULEBOOK_UPDATER_PROMPT),
        (
            "human",
            "## AI-Generated Version\n{ai_version}\n\n"
            "## User-Edited Version\n{user_version}\n\n"
            "Identify the style rules now.",
        ),
    ]
)


def _parse_json_array(text: str) -> list[str]:
    """Extract a JSON array from LLM output."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    result = json.loads(cleaned)
    if not isinstance(result, list):
        raise ValueError("Expected a JSON array")
    return [str(r) for r in result]


async def extract_style_rules(
    ai_version: str, user_version: str
) -> list[str]:
    """Compare AI-generated and user-edited resumes to extract style rules.

    Returns:
        A list of 2-3 actionable style rule strings.
    """
    llm = _get_llm()
    chain = _prompt | llm | StrOutputParser()

    logger.info("Extracting style rules from user edits")
    response = await chain.ainvoke(
        {"ai_version": ai_version, "user_version": user_version}
    )

    try:
        rules = _parse_json_array(response)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Rule extraction parse failed, retrying: %s", exc)
        retry_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", RULEBOOK_UPDATER_PROMPT),
                (
                    "human",
                    "Your previous response was not a valid JSON array. "
                    "Please output ONLY a valid JSON array of 2-3 rule strings.\n\n"
                    "## AI-Generated Version\n{ai_version}\n\n"
                    "## User-Edited Version\n{user_version}",
                ),
            ]
        )
        retry_chain = retry_prompt | llm | StrOutputParser()
        response = await retry_chain.ainvoke(
            {"ai_version": ai_version, "user_version": user_version}
        )
        rules = _parse_json_array(response)

    # Enforce 2-3 rules
    if len(rules) > 3:
        rules = rules[:3]
    elif len(rules) < 2:
        logger.warning("Fewer than 2 rules extracted (%d), returning as-is", len(rules))

    logger.info("Extracted %d style rules", len(rules))
    return rules
