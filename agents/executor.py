"""
Agentic Game-Builder AI — Executor Agent

Generates complete, playable game code (index.html, style.css, game.js)
using the Opus model.  All code is generated 100 % dynamically — no
hard-coded templates or pre-built patterns.

Uses robust regex extraction to pull code blocks from LLM markdown.
"""

import logging
import re
from typing import Dict

import yaml

from prompts.agent_prompts import EXECUTOR_PROMPT
from utils.api_helpers import call_llm

logger = logging.getLogger(__name__)

# Robust regex for fenced-code-block extraction (NEVER simple .split)
_CODE_BLOCK_RE = re.compile(
    r"```(?:html|css|javascript|js)?\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)

_LANG_TAG_RE = re.compile(
    r"```(html|css|javascript|js)\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)


def run_executor(state) -> Dict[str, str]:
    """
    Run the Executor agent.

    Parameters
    ----------
    state : GameBuilderState
        Current pipeline state (must have ``game_plan`` set).

    Returns
    -------
    dict
        ``{"index.html": "…", "style.css": "…", "game.js": "…"}``
    """
    plan_text = _format_plan(state.game_plan)

    # Include validation issues from previous attempt if retrying
    extra = ""
    if state.retry_count > 0 and state.validation_result:
        issues = state.validation_result.get("issues", [])
        if issues:
            extra = (
                "\n\n**IMPORTANT — Previous attempt failed validation. "
                "Fix these issues:**\n"
                + "\n".join(f"- {i}" for i in issues)
            )

    user_message = f"Game Plan:\n\n{plan_text}{extra}"

    raw_response = call_llm(
        agent_name="executor",
        system_prompt=EXECUTOR_PROMPT,
        user_message=user_message,
    )

    files = _parse_executor_response(raw_response)
    logger.info(
        "Executor produced %d file(s): %s",
        len(files),
        ", ".join(f"{k} ({len(v)} chars)" for k, v in files.items()),
    )
    return files


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_plan(plan: dict | None) -> str:
    """Serialise the game plan dict into YAML for the prompt."""
    if not plan:
        return "No plan available."
    try:
        return yaml.dump(plan, default_flow_style=False, sort_keys=False)
    except Exception:
        return str(plan)


def _parse_executor_response(raw: str) -> Dict[str, str]:
    """
    Extract index.html, style.css, and game.js from the LLM's markdown
    output using robust regex — never simple string splitting.
    """
    files: Dict[str, str] = {}

    # Try language-tagged blocks first
    tagged_blocks = _LANG_TAG_RE.findall(raw)
    if tagged_blocks:
        for lang, content in tagged_blocks:
            lang = lang.lower().strip()
            if lang == "html" and "index.html" not in files:
                files["index.html"] = content.strip()
            elif lang == "css" and "style.css" not in files:
                files["style.css"] = content.strip()
            elif lang in ("javascript", "js") and "game.js" not in files:
                files["game.js"] = content.strip()

    # If we're still missing files, try untagged blocks and infer by content
    if len(files) < 3:
        all_blocks = _CODE_BLOCK_RE.findall(raw)
        for block in all_blocks:
            block = block.strip()
            if not block:
                continue
            if "index.html" not in files and ("<!DOCTYPE" in block or "<html" in block):
                files["index.html"] = block
            elif "style.css" not in files and ("{" in block and ("margin" in block or "padding" in block or "body" in block or "canvas" in block)):
                files["style.css"] = block
            elif "game.js" not in files and ("function" in block or "const " in block or "var " in block or "class " in block):
                files["game.js"] = block

    # Final fallback: ensure all three keys exist
    for key in ("index.html", "style.css", "game.js"):
        if key not in files:
            logger.warning("Could not extract %s from Executor response.", key)
            files[key] = ""

    return files
