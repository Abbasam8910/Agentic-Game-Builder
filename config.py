"""
Agentic Game-Builder AI — Central Configuration

All model routing, temperature settings, token limits, and system-wide
constants are defined here.  Import this module wherever you need config.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Anthropic Model Routing
# ---------------------------------------------------------------------------

MODELS = {
    # Fast, cheap — perfect for simple conversational routing
    "clarifier": "claude-haiku-4-5-20251001",
    # Excellent at outputting structured YAML/JSON design documents
    "planner": "claude-sonnet-4-5-20250929",
    # The heavy hitter — max reasoning power for zero-shot code generation
    "executor": "claude-sonnet-4-5-20250929", # claude-opus-4-6
    # Smart enough for structural validation, cheap enough to loop
    "validator": "claude-sonnet-4-5-20250929",
}

TEMPERATURES = {
    "clarifier": 0.5,   # Natural, focused conversation
    "planner": 0.3,     # Strict YAML/JSON formatting
    "executor": 0.2,    # Deterministic code, minor creative mechanics
    "validator": 0.1,   # Ruthless, strict pattern matching
}

MAX_TOKENS = {
    "clarifier": 1024,
    "planner": 4096,
    "executor": 8192,
    "validator": 2048,
}

# ---------------------------------------------------------------------------
# System-wide constants
# ---------------------------------------------------------------------------

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
API_TIMEOUT: int = 300  # seconds
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Output directories
OUTPUT_DIR: str = os.path.join(os.path.dirname(__file__), "output")
FAILED_DIR: str = os.path.join(OUTPUT_DIR, "failed")
