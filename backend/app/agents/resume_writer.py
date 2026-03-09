"""Resume Writer Agent — premium model for ATS-optimized resume tailoring."""

from __future__ import annotations

import json
import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from app.agents.prompts import RESUME_WRITER_PROMPT
from app.config import settings

logger = logging.getLogger(__name__)

_llm: BaseChatModel | None = None


def _get_llm() -> BaseChatModel:
    """Select the best available premium model.

    Priority: OpenAI GPT-4o > Anthropic Claude 3.5 Sonnet.
    Raises RuntimeError if neither key is configured.
    """
    global _llm
    if _llm is not None:
        return _llm

    if settings.OPENAI_API_KEY:
        from langchain_openai import ChatOpenAI

        _llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.3,
            max_tokens=4096,
        )
        logger.info("Resume writer using OpenAI GPT-4o")
    elif settings.ANTHROPIC_API_KEY:
        from langchain_anthropic import ChatAnthropic

        _llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=0.3,
            max_tokens=4096,
        )
        logger.info("Resume writer using Anthropic Claude 3.5 Sonnet")
    else:
        raise RuntimeError(
            "No premium AI key configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY."
        )

    return _llm


_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", RESUME_WRITER_PROMPT),
        (
            "human",
            "## Master Resume (PII-masked)\n{master_resume}\n\n"
            "## Target Job Description (structured)\n{jd_json}\n\n"
            "## User Rulebook\n{user_rulebook}\n\n"
            "Generate the tailored resume now.",
        ),
    ]
)


async def write_tailored_resume(
    master_resume: str,
    jd_json: dict,
    user_rulebook: dict | None = None,
) -> str:
    """Generate a tailored, ATS-optimized resume.

    Args:
        master_resume: PII-masked master resume text.
        jd_json: Structured JD from the normalizer agent.
        user_rulebook: Optional dict of user style preferences.

    Returns:
        The tailored resume as plain text with PII tokens preserved.
    """
    llm = _get_llm()
    chain = _prompt | llm

    rulebook_str = json.dumps(user_rulebook, indent=2) if user_rulebook else "None provided — use defaults."
    jd_str = json.dumps(jd_json, indent=2)

    logger.info("Generating tailored resume (jd_title=%s)", jd_json.get("job_title", "unknown"))
    response = await chain.ainvoke(
        {
            "master_resume": master_resume,
            "jd_json": jd_str,
            "user_rulebook": rulebook_str,
        }
    )

    # ChatModel returns AIMessage; extract the text content
    content = response.content if hasattr(response, "content") else str(response)

    # Strip any markdown fences the model may have wrapped around the output
    if content.strip().startswith("```"):
        lines = content.strip().split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        content = "\n".join(lines).strip()

    logger.info("Tailored resume generated (%d chars)", len(content))
    return content
