"""
Test: Verify all project modules import cleanly.
"""

import importlib
import pytest


MODULES = [
    "config",
    "orchestrator",
    "agents",
    "agents.clarifier",
    "agents.planner",
    "agents.executor",
    "agents.validator",
    "prompts.agent_prompts",
    "utils",
    "utils.api_helpers",
    "utils.file_manager",
    "utils.validation",
]


@pytest.mark.parametrize("module_name", MODULES)
def test_import(module_name):
    """Each module must import without errors."""
    mod = importlib.import_module(module_name)
    assert mod is not None
