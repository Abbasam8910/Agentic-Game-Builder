"""
Agentic Game-Builder AI — API Helpers

Production-grade wrapper around the Anthropic SDK.
* @safe_llm_call decorator with exponential back-off
* Centralised client creation
* Timeout enforcement (60 s)
"""

import functools
import logging
import time

import anthropic

from config import ANTHROPIC_API_KEY, API_TIMEOUT, MODELS, TEMPERATURES, MAX_TOKENS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Anthropic client singleton
# ---------------------------------------------------------------------------

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    """Return a reusable Anthropic client."""
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. "
                "Create a .env file or export the variable."
            )
        _client = anthropic.Anthropic(
            api_key=ANTHROPIC_API_KEY,
            timeout=API_TIMEOUT,
        )
        logger.info("Anthropic client initialised.")
    return _client


# ---------------------------------------------------------------------------
# @safe_llm_call decorator
# ---------------------------------------------------------------------------

def safe_llm_call(func):
    """
    Decorator that wraps any function making Anthropic API calls with:
    * RateLimitError  → exponential back-off (2ˣ s, max 3 retries)
    * APITimeoutError → single retry after 5 s
    * APIError        → log and re-raise
    * Empty response  → raise ValueError
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

            except anthropic.RateLimitError as exc:
                wait = 2 ** attempt
                logger.warning(
                    "Rate-limited (attempt %d/%d). Retrying in %ds …",
                    attempt, max_api_retries, wait,
                )
                if attempt == max_api_retries:
                    logger.error("Rate-limit retries exhausted.")
                    raise
                time.sleep(wait)

            except anthropic.APITimeoutError:
                logger.warning(
                    "API timeout (attempt %d/%d). Retrying in 5 s …",
                    attempt, max_api_retries,
                )
                if attempt == max_api_retries:
                    logger.error("Timeout retries exhausted.")
                    raise
                time.sleep(5)

            except anthropic.APIError as exc:
                logger.error("Anthropic API error: %s", exc)
                raise

            except ValueError as exc:
                logger.error("Response validation error: %s", exc)
                raise

    return wrapper


# ---------------------------------------------------------------------------
# Convenience caller
# ---------------------------------------------------------------------------

@safe_llm_call
def call_anthropic(
    agent_name: str,
    system_prompt: str,
    user_message: str,
) -> str:
    """
    Make a single Anthropic messages-API call for the given agent.

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
        The assistant's text response.
    """
    client = get_client()
    model = MODELS[agent_name]
    temperature = TEMPERATURES[agent_name]
    max_tokens = MAX_TOKENS[agent_name]

    logger.info(
        "Calling %s  model=%s  temp=%s  max_tokens=%d",
        agent_name, model, temperature, max_tokens,
    )

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    text = response.content[0].text
    logger.info(
        "%s responded — %d chars.", agent_name, len(text),
    )
    return text
