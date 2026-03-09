"""Pipeline Orchestrator — runs the full resume tailoring workflow via LangGraph."""

from __future__ import annotations

import logging
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.company_enrichment import enrich_company
from app.agents.jd_normalizer import normalize_jd
from app.agents.qa_auditor import audit_resume
from app.agents.resume_writer import write_tailored_resume

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------

class PipelineState(TypedDict, total=False):
    # Inputs
    master_resume: str
    jd_text: str
    user_rulebook: dict | None
    company_name: str | None

    # Intermediate
    jd_json: dict
    company_context: dict | None
    masked_resume: str
    pii_mapping: dict
    draft: str

    # QA loop
    qa_result: dict
    retry_count: int

    # Final output
    final_draft: str
    qa_passed: bool
    confidence_score: int
    error: str | None


# ---------------------------------------------------------------------------
# PII helpers — gracefully degrade if pii_service doesn't exist yet
# ---------------------------------------------------------------------------

def _mask_resume(text: str) -> tuple[str, dict]:
    """Attempt to PII-mask the resume using the presidio-based pii_service.

    Returns (masked_text, pii_mapping). Falls back to identity if the
    service module is not yet available.
    """
    try:
        from app.services.pii_service import mask_pii
        return mask_pii(text)
    except ImportError:
        logger.warning(
            "pii_service not available — skipping PII masking. "
            "Create app/services/pii_service.py to enable masking."
        )
        return text, {}


def _rehydrate_resume(text: str, mapping: dict) -> str:
    """Replace PII tokens in text with original values."""
    try:
        from app.services.pii_service import rehydrate_pii
        return rehydrate_pii(text, mapping)
    except ImportError:
        if mapping:
            # Manual token replacement as fallback
            result = text
            for token, original in mapping.items():
                result = result.replace(token, original)
            return result
        return text


# ---------------------------------------------------------------------------
# Graph node functions
# ---------------------------------------------------------------------------

async def node_normalize_jd(state: PipelineState) -> dict[str, Any]:
    """Step 1: Normalise the raw job description."""
    logger.info("Pipeline step: normalize_jd")
    jd_json = await normalize_jd(state["jd_text"])
    return {"jd_json": jd_json}


async def node_enrich_company(state: PipelineState) -> dict[str, Any]:
    """Step 2: Optionally enrich company data."""
    company_name = state.get("company_name")
    if not company_name:
        logger.info("Pipeline step: enrich_company — skipped (no company name)")
        return {"company_context": None}

    logger.info("Pipeline step: enrich_company — %s", company_name)
    context = await enrich_company(company_name)
    return {"company_context": context}


async def node_mask_resume(state: PipelineState) -> dict[str, Any]:
    """Step 3: PII-mask the master resume."""
    logger.info("Pipeline step: mask_resume")
    masked, mapping = _mask_resume(state["master_resume"])
    return {"masked_resume": masked, "pii_mapping": mapping}


async def node_write_resume(state: PipelineState) -> dict[str, Any]:
    """Step 4/7: Call the premium writer agent."""
    logger.info("Pipeline step: write_resume (retry_count=%d)", state.get("retry_count", 0))

    # Merge company context into JD if available
    jd_json = dict(state["jd_json"])
    company_ctx = state.get("company_context")
    if company_ctx:
        jd_json["company_context"] = company_ctx

    # Build rulebook, merging QA violations as extra guidance on retries
    rulebook = dict(state["user_rulebook"]) if state.get("user_rulebook") else {}
    qa_result = state.get("qa_result")
    if qa_result and qa_result.get("violations"):
        rulebook["_qa_fix_instructions"] = (
            "Your previous draft FAILED QA. Fix these violations: "
            + "; ".join(qa_result["violations"])
        )

    draft = await write_tailored_resume(
        master_resume=state["masked_resume"],
        jd_json=jd_json,
        user_rulebook=rulebook or None,
    )
    return {"draft": draft}


async def node_rehydrate(state: PipelineState) -> dict[str, Any]:
    """Step 5: Replace PII tokens with original values."""
    logger.info("Pipeline step: rehydrate")
    rehydrated = _rehydrate_resume(state["draft"], state.get("pii_mapping", {}))
    return {"final_draft": rehydrated}


async def node_qa_audit(state: PipelineState) -> dict[str, Any]:
    """Step 6: Run the QA auditor."""
    logger.info("Pipeline step: qa_audit")
    result = await audit_resume(
        master_resume=state["master_resume"],
        tailored_draft=state["final_draft"],
    )
    return {
        "qa_result": result,
        "qa_passed": result["status"] == "PASS",
        "confidence_score": result["confidence_score"],
        "retry_count": state.get("retry_count", 0) + 1,
    }


# ---------------------------------------------------------------------------
# Conditional edge: retry or finish
# ---------------------------------------------------------------------------

def should_retry(state: PipelineState) -> str:
    """Decide whether to retry the writer or finish."""
    if state.get("qa_passed"):
        return "finish"
    if state.get("retry_count", 0) >= MAX_RETRIES:
        logger.warning(
            "QA still failing after %d retries — returning best effort",
            MAX_RETRIES,
        )
        return "finish"
    logger.info("QA failed — retrying writer (attempt %d)", state.get("retry_count", 0) + 1)
    return "retry"


# ---------------------------------------------------------------------------
# Build the LangGraph StateGraph
# ---------------------------------------------------------------------------

def _build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    # Add nodes
    graph.add_node("normalize_jd", node_normalize_jd)
    graph.add_node("enrich_company", node_enrich_company)
    graph.add_node("mask_resume", node_mask_resume)
    graph.add_node("write_resume", node_write_resume)
    graph.add_node("rehydrate", node_rehydrate)
    graph.add_node("qa_audit", node_qa_audit)

    # Define edges
    graph.set_entry_point("normalize_jd")
    graph.add_edge("normalize_jd", "enrich_company")
    graph.add_edge("enrich_company", "mask_resume")
    graph.add_edge("mask_resume", "write_resume")
    graph.add_edge("write_resume", "rehydrate")
    graph.add_edge("rehydrate", "qa_audit")

    # Conditional: retry or finish
    graph.add_conditional_edges(
        "qa_audit",
        should_retry,
        {
            "retry": "write_resume",
            "finish": END,
        },
    )

    return graph


# Compile once at module level
_compiled_graph = _build_graph().compile()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def run_tailoring_pipeline(
    master_resume: str,
    jd_text: str,
    user_rulebook: dict | None = None,
    company_name: str | None = None,
) -> dict:
    """Execute the full resume tailoring pipeline.

    Args:
        master_resume: The candidate's full master resume (plain text).
        jd_text: Raw job description text.
        user_rulebook: Optional dict of user style preferences.
        company_name: Optional company name for enrichment.

    Returns:
        dict with keys:
        - final_draft: The tailored resume text (PII rehydrated).
        - qa_result: Full QA audit result dict.
        - qa_passed: bool indicating if QA passed.
        - confidence_score: int 0-100.
        - jd_json: The structured JD.
        - company_context: Company enrichment data or None.
        - retry_count: Number of QA-retry cycles used.
        - error: Error message if something went wrong, else None.
    """
    logger.info("Starting tailoring pipeline")

    initial_state: PipelineState = {
        "master_resume": master_resume,
        "jd_text": jd_text,
        "user_rulebook": user_rulebook,
        "company_name": company_name,
        "retry_count": 0,
        "error": None,
    }

    try:
        final_state = await _compiled_graph.ainvoke(initial_state)
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        return {
            "final_draft": "",
            "qa_result": {},
            "qa_passed": False,
            "confidence_score": 0,
            "jd_json": {},
            "company_context": None,
            "retry_count": 0,
            "error": str(exc),
        }

    return {
        "final_draft": final_state.get("final_draft", ""),
        "qa_result": final_state.get("qa_result", {}),
        "qa_passed": final_state.get("qa_passed", False),
        "confidence_score": final_state.get("confidence_score", 0),
        "jd_json": final_state.get("jd_json", {}),
        "company_context": final_state.get("company_context"),
        "retry_count": final_state.get("retry_count", 0),
        "error": final_state.get("error"),
    }
