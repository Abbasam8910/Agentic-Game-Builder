"""
Agentic Game-Builder AI — Validator Agent

Two-layer validation:
1. **Deterministic checks** (utils/validation.py) — fast, regex-based
2. **LLM-based review** (Sonnet) — catches semantic issues the regex misses

Returns a unified ``{"is_valid": bool, "issues": [...], "suggestions": [...]}``
"""

import json
import logging
from typing import Dict

from prompts.agent_prompts import VALIDATOR_PROMPT
from utils.api_helpers import call_llm
from utils.validation import run_all_checks

logger = logging.getLogger(__name__)


def run_validator(state) -> Dict:
    """
    Run the Validator agent.

    Parameters
    ----------
    state : GameBuilderState
        Current pipeline state (must have ``generated_files`` set).

    Returns
    -------
    dict
        ``{"is_valid": bool, "issues": [...], "suggestions": [...]}``
    """
    files = state.generated_files

    # ── Layer 1: deterministic structural checks ────────────────────────
    struct_ok, struct_issues = run_all_checks(files, state.game_plan)
    if not struct_ok:
        logger.warning("Structural validation failed: %s", struct_issues)
        return {
            "is_valid": False,
            "issues": struct_issues,
            "suggestions": ["Fix the structural issues above and regenerate."],
        }

    # ── Layer 2: LLM-based semantic review ──────────────────────────────
    code_summary = _build_code_summary(files)
    raw_response = call_llm(
        agent_name="validator",
        system_prompt=VALIDATOR_PROMPT,
        user_message=code_summary,
    )

    result = _parse_validator_response(raw_response)
    logger.info("Validator result — valid=%s, issues=%d", result["is_valid"], len(result["issues"]))
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_code_summary(files: Dict[str, str]) -> str:
    """Assemble the generated files into a single string for the LLM."""
    parts = []
    for fname in ("index.html", "style.css", "game.js"):
        content = files.get(fname, "")
        parts.append(f"=== {fname} ===\n{content}\n")
    return "\n".join(parts)


def _parse_validator_response(raw: str) -> Dict:
    """Parse the Validator's JSON response with fallback handling."""
    text = raw.strip()

    # Strip markdown fences
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON in response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                data = json.loads(text[start:end])
            except json.JSONDecodeError:
                logger.error("Could not parse Validator JSON response.")
                return {
                    "is_valid": False,
                    "issues": ["Validator response was not valid JSON — treating as failure."],
                    "suggestions": [],
                }
        else:
            return {
                "is_valid": False,
                "issues": ["Validator response was not valid JSON — treating as failure."],
                "suggestions": [],
            }

    return {
        "is_valid": data.get("is_valid", False),
        "issues": data.get("issues", []),
        "suggestions": data.get("suggestions", []),
    }
