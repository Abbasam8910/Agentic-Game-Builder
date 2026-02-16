"""
Agentic Game-Builder AI — File Manager

Handles persisting generated game files and failed attempts to disk.
"""

import logging
import os
import re
from datetime import datetime

from config import OUTPUT_DIR, FAILED_DIR

logger = logging.getLogger(__name__)


def _sanitise_name(name: str) -> str:
    """Turn a human-readable title into a filesystem-safe directory name."""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = name.strip("-")
    return name or "unnamed-game"


def save_game_files(files: dict[str, str], game_title: str) -> str:
    """
    Write generated game files to ``output/<game-title>/``.

    Parameters
    ----------
    files : dict
        Mapping of filename → content (e.g. ``{"index.html": "…", …}``).
    game_title : str
        Human-readable game title.

    Returns
    -------
    str
        Absolute path to the output directory.
    """
    dir_name = _sanitise_name(game_title)
    out_path = os.path.join(OUTPUT_DIR, dir_name)
    os.makedirs(out_path, exist_ok=True)

    for filename, content in files.items():
        filepath = os.path.join(out_path, filename)
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(content)
        logger.info("Saved %s (%d bytes)", filepath, len(content))

    logger.info("All game files saved to %s", out_path)
    return out_path


def save_failed_attempt(files: dict[str, str], attempt_number: int) -> str:
    """
    Save a failed code-generation attempt for debugging.

    Files are written to ``output/failed/<timestamp>-attempt-<N>/``.

    Returns
    -------
    str
        Absolute path to the failed-attempt directory.
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dir_name = f"{timestamp}-attempt-{attempt_number}"
    fail_path = os.path.join(FAILED_DIR, dir_name)
    os.makedirs(fail_path, exist_ok=True)

    for filename, content in files.items():
        filepath = os.path.join(fail_path, filename)
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(content)
        logger.info("Saved failed file %s", filepath)

    logger.warning("Failed attempt #%d saved to %s", attempt_number, fail_path)
    return fail_path
