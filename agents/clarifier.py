"""
Agentic Game-Builder AI — Clarifier Agent

Analyses user input, detects already-specified fields, and generates
smart clarification questions.  Returns structured JSON with requirements
and optional questions for the interactive loop in main.py.
"""

import json
import logging
from typing import Dict

from prompts.agent_prompts import CLARIFIER_PROMPT
from utils.api_helpers import call_llm

logger = logging.getLogger(__name__)


def run_clarifier(state) -> Dict:
    """
    Run the Clarifier agent.

    Parameters
    ----------
    state : GameBuilderState
        Current pipeline state.

    Returns
    -------
    dict
        ``{"is_complete": bool, "questions": [...], "requirements": {...}}``
    """
    # Build user message with all context so far
    parts = [f"Game idea: {state.user_input}"]

    if state.conversation_history:
        parts.append("\nPrevious conversation:")
        for msg in state.conversation_history:
            role = msg["role"].capitalize()
            parts.append(f"  {role}: {msg['content']}")

    if state.requirements:
        parts.append(f"\nCurrent requirements (partial): {json.dumps(state.requirements)}")

    user_message = "\n".join(parts)

    # Call the LLM
    raw_response = call_llm(
        agent_name="clarifier",
        system_prompt=CLARIFIER_PROMPT,
        user_message=user_message,
    )

    # Parse JSON response
    result = _parse_clarifier_response(raw_response)
    logger.info(
        "Clarifier result — complete=%s, questions=%d",
        result.get("is_complete"),
        len(result.get("questions", [])),
    )
    return result


def _parse_clarifier_response(raw: str) -> Dict:
    """
    Parse the Clarifier's JSON response, handling wrapper text or
    markdown fences the LLM might add.
    """
    text = raw.strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last fence lines
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                data = json.loads(text[start:end])
            except json.JSONDecodeError:
                logger.error("Failed to parse Clarifier response as JSON.")
                return {
                    "is_complete": False,
                    "questions": ["Could you describe your game idea in more detail?"],
                    "requirements": None,
                }
        else:
            logger.error("No JSON object found in Clarifier response.")
            return {
                "is_complete": False,
                "questions": ["Could you describe your game idea in more detail?"],
                "requirements": None,
            }

    # Normalise
    return {
        "is_complete": data.get("is_complete", False),
        "questions": data.get("questions", []),
        "requirements": data.get("requirements"),
    }
