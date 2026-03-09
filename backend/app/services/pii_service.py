from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# ── Entity types we care about and their token prefixes ─────────────────
_ENTITY_PREFIX_MAP: Dict[str, str] = {
    "PERSON": "PERSON",
    "EMAIL_ADDRESS": "EMAIL",
    "PHONE_NUMBER": "PHONE",
    "LOCATION": "ADDRESS",
    "ADDRESS": "ADDRESS",
    "ORGANIZATION": "ORG",
    "URL": "URL",
    "US_SSN": "SSN",
    "CREDIT_CARD": "CC",
}

_SUPPORTED_ENTITIES = list(_ENTITY_PREFIX_MAP.keys())

# ── Lazy-initialised engines ────────────────────────────────────────────
_analyzer = None
_anonymizer = None


def _get_analyzer():
    """Return a PresidioAnalyzerEngine, falling back to regex if spaCy model is missing."""
    global _analyzer
    if _analyzer is not None:
        return _analyzer

    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.nlp_engine import NlpEngineProvider

    try:
        provider = NlpEngineProvider(nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
        })
        nlp_engine = provider.create_engine()
        _analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
        logger.info("PII analyzer initialised with spaCy en_core_web_lg")
    except (ImportError, OSError) as exc:
        logger.warning(
            "spaCy model en_core_web_lg unavailable (%s); "
            "falling back to regex-based PII detection",
            exc,
        )
        _analyzer = AnalyzerEngine(supported_languages=["en"])

    return _analyzer


def _get_anonymizer():
    global _anonymizer
    if _anonymizer is not None:
        return _anonymizer

    from presidio_anonymizer import AnonymizerEngine

    _anonymizer = AnonymizerEngine()
    return _anonymizer


# ── Public API ──────────────────────────────────────────────────────────

def mask_pii(text: str) -> Tuple[str, dict]:
    """Detect and replace PII with deterministic placeholder tokens.

    Returns
    -------
    masked_text : str
        Text with PII replaced by tokens like ``<PERSON_1>``, ``<EMAIL_1>``.
    token_map : dict
        Mapping of each token to the original PII value,
        e.g. ``{"<PERSON_1>": "John Doe", "<EMAIL_1>": "john@example.com"}``.
    """
    analyzer = _get_analyzer()

    results = analyzer.analyze(
        text=text,
        language="en",
        entities=_SUPPORTED_ENTITIES,
    )

    # Sort by start position (descending) so replacements don't shift offsets
    results = sorted(results, key=lambda r: r.start, reverse=True)

    # Counters per entity prefix to create sequential tokens
    counters: Dict[str, int] = defaultdict(int)
    # Track already-seen (entity_type, value) pairs to reuse the same token
    seen: Dict[Tuple[str, str], str] = {}
    token_map: Dict[str, str] = {}
    masked_text = text

    for result in results:
        original_value = text[result.start : result.end]
        entity_type: str = result.entity_type
        prefix: str = _ENTITY_PREFIX_MAP.get(entity_type, entity_type)

        lookup_key = (prefix, original_value)
        if lookup_key in seen:
            token = seen[lookup_key]
        else:
            counters[prefix] += 1
            token = f"<{prefix}_{counters[prefix]}>"
            seen[lookup_key] = token
            token_map[token] = original_value

        masked_text = masked_text[: result.start] + token + masked_text[result.end :]

    return masked_text, token_map


def rehydrate_pii(masked_text: str, token_map: dict) -> str:
    """Replace placeholder tokens with the original PII values.

    Parameters
    ----------
    masked_text : str
        Text containing tokens such as ``<PERSON_1>``.
    token_map : dict
        Mapping produced by :func:`mask_pii`.

    Returns
    -------
    str
        Text with all tokens replaced by their original values.
    """
    result = masked_text
    # Sort tokens longest-first to avoid partial replacement collisions
    for token in sorted(token_map, key=len, reverse=True):
        result = result.replace(token, token_map[token])
    return result
