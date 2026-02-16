"""
Agentic Game-Builder AI — API Helpers

Production-grade wrapper around the Google GenAI SDK (Gemini).
* @safe_llm_call decorator with exponential back-off
* Centralised client creation
* Provider-agnostic retry logic
"""

import functools
import logging
import time

from google import genai
from google.genai import types

from config import GOOGLE_API_KEY, MODEL_CONFIG

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Google GenAI client singleton
# ---------------------------------------------------------------------------

_client: genai.Client | None = None


def get_client() -> genai.Client:
    """Return a reusable Google GenAI client."""
    global _client
    if _client is None:
        if not GOOGLE_API_KEY:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. "
                "Create a .env file or export the variable."
            )
        _client = genai.Client(api_key=GOOGLE_API_KEY)
        logger.info("Google GenAI client initialised.")
    return _client


# ---------------------------------------------------------------------------
# @safe_llm_call decorator
# ---------------------------------------------------------------------------

def safe_llm_call(func):
    """
    Decorator that wraps any function making Gemini API calls with:
    * Rate-limit (429)    → exponential back-off (2ˣ s, max 3 retries)
    * Timeout / Deadline  → single retry after 5 s
    * Other API errors    → log and re-raise
    * Empty response      → raise ValueError
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        max_api_retries = 3
        for attempt in range(1, max_api_retries + 1):
            try:
                result = func(*args, **kwargs)

                # Guard: empty response
                if result is None or (isinstance(result, str) and len(result.strip()) == 0):
                    raise ValueError("LLM returned an empty response.")

                return result

            except ValueError:
                raise

            except Exception as exc:
                exc_str = str(exc).lower()

                # Rate-limit / quota / server-overload errors
                if any(kw in exc_str for kw in ("429", "resource", "rate", "quota", "exhausted", "503", "500", "unavailable", "server error", "overloaded")):
                    wait = 2 ** attempt
                    logger.warning(
                        "Rate-limited (attempt %d/%d). Retrying in %ds …",
                        attempt, max_api_retries, wait,
                    )
                    if attempt == max_api_retries:
                        logger.error("Rate-limit retries exhausted.")
                        raise
                    time.sleep(wait)

                # Timeout errors
                elif any(kw in exc_str for kw in ("timeout", "deadline", "timed out")):
                    logger.warning(
                        "API timeout (attempt %d/%d). Retrying in 5 s …",
                        attempt, max_api_retries,
                    )
                    if attempt == max_api_retries:
                        logger.error("Timeout retries exhausted.")
                        raise
                    time.sleep(5)

                # All other errors — log and re-raise immediately
                else:
                    logger.error("API error: %s", exc)
                    raise

    return wrapper


# ---------------------------------------------------------------------------
# Convenience caller
# ---------------------------------------------------------------------------

@safe_llm_call
def call_llm(
    agent_name: str,
    system_prompt: str,
    user_message: str,
) -> str:
    """
    Make a single Google Gemini API call for the given agent.

    Parameters
    ----------
    agent_name : str
        One of 'clarifier', 'planner', 'executor', 'validator'.
    system_prompt : str
        The system-level instruction for the agent.
    user_message : str
        The user-facing prompt / context.

    Returns
    -------
    str
        The model's text response.
    """
    client = get_client()
    cfg = MODEL_CONFIG[agent_name]

    model = cfg["model"]
    temperature = cfg["temperature"]
    max_output_tokens = cfg["max_output_tokens"]
    top_p = cfg.get("top_p", 0.9)
    top_k = cfg.get("top_k", 40)

    logger.info(
        "Calling %s  model=%s  temp=%s  max_tokens=%d",
        agent_name, model, temperature, max_output_tokens,
    )

    response = client.models.generate_content(
        model=model,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            top_p=top_p,
            top_k=top_k,
        ),
    )

    text = response.text
    logger.info(
        "%s responded — %d chars.", agent_name, len(text),
    )
    return text
