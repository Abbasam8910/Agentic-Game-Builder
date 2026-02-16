"""
Agentic Game-Builder AI — Planner Agent

Takes finalised requirements and produces a structured JSON game design
document, including framework selection, technical architecture, asset
specs, controls, and implementation notes.
"""

import json
import logging
from typing import Dict

from prompts.agent_prompts import PLANNER_PROMPT
from utils.api_helpers import call_llm

logger = logging.getLogger(__name__)


def run_planner(state) -> Dict:
    """
    Run the Planner agent.

    Parameters
    ----------
    state : GameBuilderState
        Current pipeline state (must have ``requirements`` set).

    Returns
    -------
    dict
        Parsed game design document.
    """
    # Build a concise summary of requirements for the planner
    req_text = _format_requirements(state.requirements)
    user_message = (
        f"Create a complete game design document for the following game:\n\n"
        f"{req_text}\n\n"
        f"Original user idea: {state.user_input}"
    )

    raw_response = call_llm(
        agent_name="planner",
        system_prompt=PLANNER_PROMPT,
        user_message=user_message,
    )

    plan = _parse_planner_response(raw_response)
    logger.info("Game plan generated — title: %s", plan.get("metadata", {}).get("game_title", "?"))
    return plan


def _format_requirements(requirements: dict | None) -> str:
    """Turn the requirements dict into a readable string for the prompt."""
    if not requirements:
        return "No structured requirements available."

    lines = []
    for key, value in requirements.items():
        if value is not None:
            label = key.replace("_", " ").title()
            if isinstance(value, list):
                lines.append(f"- {label}: {', '.join(str(v) for v in value)}")
            else:
                lines.append(f"- {label}: {value}")
    return "\n".join(lines) if lines else "No structured requirements available."


def _parse_planner_response(raw: str) -> Dict:
    """
    Parse the Planner's JSON response.

    Handles markdown fences the LLM might wrap around the JSON.
    """
    text = raw.strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # Fallback: try to find JSON object in the response
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        try:
            data = json.loads(text[start:end])
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    logger.error("Could not parse any JSON from Planner response. Using fallback.")
    return {
        "metadata": {
            "game_title": "Generated Game",
            "framework": "vanilla-js",
        },
        "raw_plan": text,
    }
