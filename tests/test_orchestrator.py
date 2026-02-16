"""
Test: Orchestrator state, stopping criteria, and retry logic.
"""

import pytest
from orchestrator import GameBuilderState
from config import MAX_RETRIES


class TestGameBuilderState:
    """Pydantic V2 state model tests."""

    def test_default_state(self):
        state = GameBuilderState(user_input="test game")
        assert state.user_input == "test game"
        assert state.current_phase == "clarifying"
        assert state.is_complete is False
        assert state.retry_count == 0
        assert state.generated_files == {}
        assert state.conversation_history == []

    def test_validate_assignment(self):
        state = GameBuilderState(user_input="test")
        state.current_phase = "planning"
        assert state.current_phase == "planning"

    def test_retry_count_bounds(self):
        state = GameBuilderState(user_input="test")
        state.retry_count = 3
        assert state.retry_count == 3

        with pytest.raises(Exception):
            # Pydantic should reject retry_count > 3
            state.retry_count = 4

    def test_retry_count_negative(self):
        with pytest.raises(Exception):
            GameBuilderState(user_input="test", retry_count=-1)

    def test_requirements_optional(self):
        state = GameBuilderState(user_input="test")
        assert state.requirements is None
        state.requirements = {"game_type": "platformer"}
        assert state.requirements["game_type"] == "platformer"


class TestRetryLogic:
    """Test the retry count and MAX_RETRIES constant."""

    def test_max_retries_is_positive(self):
        assert MAX_RETRIES > 0

    def test_max_retries_default(self):
        assert MAX_RETRIES == 3

    def test_state_retry_increments(self):
        state = GameBuilderState(user_input="test")
        for i in range(MAX_RETRIES):
            state.retry_count = i + 1
        assert state.retry_count == MAX_RETRIES


class TestStoppingCriteria:
    """Verify requirements-completeness logic."""

    def test_incomplete_requirements(self):
        reqs = {"game_type": "shooter", "core_mechanic": None}
        filled = sum(1 for v in reqs.values() if v is not None)
        assert filled < 3

    def test_complete_requirements(self):
        reqs = {
            "game_type": "platformer",
            "core_mechanic": "jump and collect",
            "win_condition": "collect all stars",
            "control_scheme": "arrow keys",
        }
        filled = sum(1 for v in reqs.values() if v is not None)
        assert filled >= 3
