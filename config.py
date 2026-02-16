"""
Agentic Game-Builder AI — Central Configuration

All model routing, temperature profiles, token budgets, and
environment-driven constants live here.  Every other module reads from
this file — never hard-codes its own values.

LLM Provider: Google Gemini (via google-genai SDK)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Model Configuration — per-agent routing
# ---------------------------------------------------------------------------

MODEL_CONFIG = {
    "clarifier": {
        "model": "gemini-2.5-flash-lite",
        "temperature": 0.3,
        "max_output_tokens": 2048,
        "top_p": 0.9,
        "top_k": 40,
    },
    "planner": {
        "model": "gemini-2.5-flash",
        "temperature": 0.2,
        "max_output_tokens": 4096,
        "top_p": 0.9,
        "top_k": 40,
    },
    "executor": {
        "model": "gemini-2.5-flash", # gemini-2.5-pro
        "temperature": 0.2,
        "max_output_tokens": 8192,
        "top_p": 0.9,
        "top_k": 40,
    },
    "validator": {
        "model": "gemini-2.5-flash",
        "temperature": 0.1,
        "max_output_tokens": 3072,
        "top_p": 0.85,
        "top_k": 40,
    },
}

# ---------------------------------------------------------------------------
# Environment-driven constants
# ---------------------------------------------------------------------------

GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
API_TIMEOUT: int = 300  # seconds
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Output directories
OUTPUT_DIR: str = os.path.join(os.path.dirname(__file__), "output")
FAILED_DIR: str = os.path.join(OUTPUT_DIR, "failed")
