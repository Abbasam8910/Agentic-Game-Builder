"""
Agentic Game-Builder AI — Master Orchestrator

Custom sequential orchestrator using a while-loop with Pydantic V2 state.
Pipeline: clarifier() → planner() → executor() → validator() → retry_check()
"""

import logging
from typing import Optional, List, Dict

from pydantic import BaseModel, Field, ConfigDict

from config import MAX_RETRIES
from agents.clarifier import run_clarifier
from agents.planner import run_planner
from agents.executor import run_executor
from agents.validator import run_validator
from utils.file_manager import save_game_files, save_failed_attempt

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic V2 State Schema
# ---------------------------------------------------------------------------

class GameBuilderState(BaseModel):
    """Immutable-ish state object passed through the entire pipeline."""

    user_input: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    clarification_questions: List[str] = Field(default_factory=list)
    user_responses: List[str] = Field(default_factory=list)
    requirements: Optional[Dict] = None
    game_plan: Optional[Dict] = None
    generated_files: Dict[str, str] = Field(default_factory=dict)
    current_phase: str = "clarifying"
    is_complete: bool = False
    validation_result: Optional[Dict] = None
    retry_count: int = Field(default=0, ge=0, le=3)

    model_config = ConfigDict(validate_assignment=True)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class GameBuilderOrchestrator:
    """
    Drives the agent pipeline in a sequential while-loop.

    Phases
    ------
    clarifying → planning → executing → validating → (complete | retry)
    """

    def __init__(self):
        self.state: Optional[GameBuilderState] = None

    # -- public entry point -------------------------------------------------

    def run(self, user_input: str) -> GameBuilderState:
        """Execute the full pipeline and return final state."""
        self.state = GameBuilderState(user_input=user_input)
        logger.info("Orchestrator initialised — starting pipeline.")

        while not self.state.is_complete:
            phase = self.state.current_phase
            logger.info("Current phase: %s", phase)

            if phase == "clarifying":
                self._run_clarifier()
            elif phase == "planning":
                self._run_planner()
            elif phase == "executing":
                self._run_executor()
            elif phase == "validating":
                self._run_validator()
            else:
                logger.error("Unknown phase '%s' — aborting.", phase)
                break

        return self.state

    # -- phase runners ------------------------------------------------------

    def _run_clarifier(self):
        """Run the Clarifier agent — returns questions for main.py to present."""
        logger.info("Running Clarifier agent …")
        result = run_clarifier(self.state)
        self.state.requirements = result.get("requirements")
        self.state.clarification_questions = result.get("questions", [])

        if result.get("is_complete", False):
            logger.info("Requirements complete — moving to planning.")
            self.state.current_phase = "planning"
        else:
            # main.py will handle the interactive loop and call
            # resume_after_clarification() once the user has answered.
            logger.info(
                "Clarifier returned %d question(s) — waiting for user.",
                len(self.state.clarification_questions),
            )

    def resume_after_clarification(self, responses: List[str]):
        """Called by main.py after the user answers clarification questions."""
        self.state.user_responses.extend(responses)
        for q, a in zip(self.state.clarification_questions, responses):
            self.state.conversation_history.append(
                {"role": "assistant", "content": q}
            )
            self.state.conversation_history.append(
                {"role": "user", "content": a}
            )
        # Re-run clarifier with the new info
        self.state.clarification_questions = []

    def _run_planner(self):
        """Run the Planner agent — produces a structured game design."""
        logger.info("Running Planner agent …")
        plan = run_planner(self.state)
        self.state.game_plan = plan
        self.state.current_phase = "executing"
        logger.info("Game plan generated — moving to execution.")

    def _run_executor(self):
        """Run the Executor agent — generates game code files."""
        logger.info("Running Executor agent …")
        files = run_executor(self.state)
        self.state.generated_files = files
        self.state.current_phase = "validating"
        logger.info("Code generated — moving to validation.")

    def _run_validator(self):
        """Run the Validator agent and decide: done or retry."""
        logger.info("Running Validator agent (attempt %d) …", self.state.retry_count + 1)
        result = run_validator(self.state)
        self.state.validation_result = result

        if result.get("is_valid", False):
            logger.info("✅ Validation passed!")
            self._save_output()
            self.state.is_complete = True
        else:
            self._handle_retry(result)

    # -- helpers ------------------------------------------------------------

    def _handle_retry(self, validation_result: Dict):
        """Increment retry counter, decide whether to retry or bail."""
        self.state.retry_count += 1
        issues = validation_result.get("issues", [])
        logger.warning(
            "Validation failed (attempt %d/%d). Issues: %s",
            self.state.retry_count,
            MAX_RETRIES,
            "; ".join(issues) if issues else "unknown",
        )

        if self.state.retry_count >= MAX_RETRIES:
            logger.warning(
                "⚠️  Max retries (%d) reached — saving best available code.",
                MAX_RETRIES,
            )
            self._save_failed()
            # Still try to save whatever we have as the final output
            if self.state.generated_files:
                self._save_output()
            self.state.is_complete = True
        else:
            logger.info("Retrying execution …")
            self.state.current_phase = "executing"

    def _save_output(self):
        """Persist the generated game files to the output directory."""
        title = "generated-game"
        if self.state.game_plan and isinstance(self.state.game_plan, dict):
            metadata = self.state.game_plan.get("metadata", {})
            title = metadata.get("game_title", title)
        save_game_files(self.state.generated_files, title)

    def _save_failed(self):
        """Persist failed attempts for debugging."""
        if self.state.generated_files:
            save_failed_attempt(
                self.state.generated_files,
                self.state.retry_count,
            )
