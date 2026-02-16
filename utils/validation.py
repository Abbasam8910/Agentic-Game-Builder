"""
Agentic Game-Builder AI — Code Validation Utilities

Structural checks applied to generated game code *before* the LLM-based
Validator agent runs.  These are cheap, deterministic, and fast.
"""

import logging
import re
from typing import Tuple, List

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Robust markdown code-block extraction (regex, NOT string splitting)
# ---------------------------------------------------------------------------

_CODE_BLOCK_RE = re.compile(
    r"```(?:html|css|javascript|js)?\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)


def extract_code_blocks(text: str) -> List[str]:
    """
    Extract all fenced code blocks from LLM markdown output.

    Uses a robust regex pattern — never simple ``.split("```")``.
    """
    return _CODE_BLOCK_RE.findall(text)


# ---------------------------------------------------------------------------
# Completeness checks
# ---------------------------------------------------------------------------

_INCOMPLETE_PATTERNS = [
    r"\bTODO\b",
    r"//\s*implement",
    r"//\s*add\s",
    r"PLACEHOLDER",
    r"function\s+\w+\s*\(\s*\)\s*\{\s*\}",  # empty function body
    r"=>\s*\{\s*\}",                          # empty arrow function
]


def check_completeness(code: str) -> Tuple[bool, List[str]]:
    """
    Scan code for TODO / placeholder / stub patterns.

    Returns
    -------
    (is_complete, issues)
    """
    issues: List[str] = []
    for pattern in _INCOMPLETE_PATTERNS:
        matches = re.findall(pattern, code, re.IGNORECASE)
        if matches:
            issues.append(f"Found incomplete pattern '{pattern}': {matches[:3]}")

    return (len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# HTML structure validation
# ---------------------------------------------------------------------------

def validate_html_structure(html: str) -> Tuple[bool, List[str]]:
    """Check that the HTML file has the essential boilerplate."""
    issues: List[str] = []

    if "<!DOCTYPE html>" not in html and "<!doctype html>" not in html:
        issues.append("Missing <!DOCTYPE html>")
    if "<canvas" not in html.lower() and "phaser" not in html.lower():
        issues.append("Missing <canvas> element (or Phaser container)")
    if "<script" not in html.lower():
        issues.append("Missing <script> tag")

    return (len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# JS structure validation
# ---------------------------------------------------------------------------

def validate_js_structure(js: str) -> Tuple[bool, List[str]]:
    """Check that game.js contains the minimum expected constructs."""
    issues: List[str] = []

    has_game_loop = (
        "requestAnimationFrame" in js
        or "setInterval" in js
        or re.search(r"function\s+update\s*\(", js) is not None
        or "Phaser.Game" in js
    )
    if not has_game_loop:
        issues.append("No game loop detected (requestAnimationFrame / update / Phaser)")

    has_events = "addEventListener" in js or "this.input" in js or "cursors" in js
    if not has_events:
        issues.append("No input event listeners detected")

    return (len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# Framework consistency
# ---------------------------------------------------------------------------

def check_framework_consistency(
    plan: dict,
    html: str,
    js: str,
) -> Tuple[bool, List[str]]:
    """Ensure plan-specified framework matches the generated code."""
    issues: List[str] = []
    framework = ""

    if isinstance(plan, dict):
        tech = plan.get("technical_architecture", {})
        choice = tech.get("framework_choice", {})
        framework = choice.get("selected", "").lower()
        if not framework:
            # fallback: check metadata
            metadata = plan.get("metadata", {})
            framework = metadata.get("framework", "").lower()

    if "phaser" in framework:
        if "Phaser" not in js and "phaser" not in html.lower():
            issues.append("Plan specifies Phaser but code does not use it")
    elif "vanilla" in framework:
        if "Phaser" in js:
            issues.append("Plan specifies Vanilla JS but code imports Phaser")

    return (len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# Aggregate validation
# ---------------------------------------------------------------------------

def run_all_checks(
    files: dict[str, str],
    plan: dict | None = None,
) -> Tuple[bool, List[str]]:
    """Run every structural check and return aggregated results."""
    all_issues: List[str] = []

    # File presence
    for required in ("index.html", "style.css", "game.js"):
        if required not in files or not files[required].strip():
            all_issues.append(f"Missing or empty file: {required}")

    if all_issues:
        return False, all_issues

    # Minimum code length
    for fname, content in files.items():
        if len(content.strip()) < 100:
            all_issues.append(f"{fname} is suspiciously short ({len(content)} chars)")

    # Completeness
    for fname in ("index.html", "game.js"):
        ok, issues = check_completeness(files[fname])
        if not ok:
            all_issues.extend([f"[{fname}] {i}" for i in issues])

    # HTML structure
    ok, issues = validate_html_structure(files["index.html"])
    if not ok:
        all_issues.extend([f"[index.html] {i}" for i in issues])

    # JS structure
    ok, issues = validate_js_structure(files["game.js"])
    if not ok:
        all_issues.extend([f"[game.js] {i}" for i in issues])

    # Framework consistency
    if plan:
        ok, issues = check_framework_consistency(plan, files["index.html"], files["game.js"])
        if not ok:
            all_issues.extend(issues)

    return (len(all_issues) == 0, all_issues)
