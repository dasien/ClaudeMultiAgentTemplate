"""
Pytest configuration and fixtures for CMAT tests.

Markers:
    @pytest.mark.requires_claude: Tests that require Claude CLI to be available
    @pytest.mark.slow: Tests that take longer to run

Run tests:
    pytest                           # Run all tests (skips Claude tests if unavailable)
    pytest -m "not requires_claude"  # Run only offline tests
    pytest -m requires_claude        # Run only Claude tests
    pytest --run-claude              # Force run Claude tests even if CLI check fails
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Generator

import pytest


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-claude",
        action="store_true",
        default=False,
        help="Run tests that require Claude CLI",
    )


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "requires_claude: mark test as requiring Claude CLI"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Skip Claude tests if CLI not available (unless --run-claude)."""
    if config.getoption("--run-claude"):
        return

    # Check if Claude CLI is available
    claude_available = shutil.which("claude") is not None

    skip_claude = pytest.mark.skip(reason="Claude CLI not available (use --run-claude to force)")

    for item in items:
        if "requires_claude" in item.keywords and not claude_available:
            item.add_marker(skip_claude)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def cmat_test_env(temp_dir: Path) -> Generator[Path, None, None]:
    """
    Create a complete CMAT test environment with all required directories.

    Returns the base path for the test environment.
    """
    # Create directory structure
    (temp_dir / ".claude/agents").mkdir(parents=True)
    (temp_dir / ".claude/skills").mkdir(parents=True)
    (temp_dir / ".claude/data").mkdir(parents=True)
    (temp_dir / ".claude/logs").mkdir(parents=True)
    (temp_dir / ".claude/docs").mkdir(parents=True)
    (temp_dir / "enhancements").mkdir(parents=True)

    # Create empty queue file
    queue_data = {
        "queue_metadata": {
            "created": "2025-01-01T00:00:00Z",
            "version": "3.0.0",
            "description": "Task queue for multi-agent development system"
        },
        "tasks": [],
        "agent_status": {},
    }
    with open(temp_dir / ".claude/data/task_queue.json", "w") as f:
        json.dump(queue_data, f)

    # Create empty agents.json
    with open(temp_dir / ".claude/agents/agents.json", "w") as f:
        json.dump({"agents": []}, f)

    # Create empty skills.json
    with open(temp_dir / ".claude/skills/skills.json", "w") as f:
        json.dump({"skills": []}, f)

    # Create empty workflow templates
    with open(temp_dir / ".claude/data/workflow_templates.json", "w") as f:
        json.dump({}, f)

    # Create empty learnings file
    with open(temp_dir / ".claude/data/learnings.json", "w") as f:
        json.dump({"version": "1.0.0", "learnings": []}, f)

    # Create tools.json with default tools
    tools_data = {
        "claude_code_tools": [
            {
                "name": "Read",
                "display_name": "Read Files",
                "description": "Read file contents from filesystem",
            },
            {
                "name": "Write",
                "display_name": "Write Files",
                "description": "Create or overwrite files",
            },
            {
                "name": "Bash",
                "display_name": "Execute Shell Commands",
                "description": "Execute shell commands and scripts",
            },
        ]
    }
    with open(temp_dir / ".claude/data/tools.json", "w") as f:
        json.dump(tools_data, f)

    # Create models.json with default model
    models_data = {
        "models": {
            "claude-sonnet-4.5": {
                "pattern": "*sonnet-4-5*|*sonnet-4*",
                "name": "Claude Sonnet 4.5",
                "description": "Balanced model for most tasks",
                "max_tokens": 200000,
                "pricing": {
                    "input": 3.00,
                    "output": 15.00,
                    "cache_write": 3.75,
                    "cache_read": 0.30,
                    "currency": "USD",
                    "per_tokens": 1000000,
                },
            }
        },
        "default_model": "claude-sonnet-4.5",
        "metadata": {
            "last_updated": "2025-01-01",
            "pricing_source": "https://www.anthropic.com/pricing",
        },
    }
    with open(temp_dir / ".claude/data/models.json", "w") as f:
        json.dump(models_data, f)

    # Create minimal TASK_PROMPT_DEFAULTS.md
    defaults_content = """# TASK_PROMPT_DEFAULTS

# ANALYSIS_TEMPLATE

You are ${agent} analyzing ${source_file}.

Task: ${task_description}

===END_TEMPLATE===

# IMPLEMENTATION_TEMPLATE

You are ${agent} implementing ${task_description}.

===END_TEMPLATE===
"""
    with open(temp_dir / ".claude/docs/TASK_PROMPT_DEFAULTS.md", "w") as f:
        f.write(defaults_content)

    yield temp_dir


@pytest.fixture
def sample_agent_md(cmat_test_env: Path) -> Path:
    """Create a sample agent markdown file."""
    agent_content = """---
name: "Test Agent"
role: "testing"
description: "An agent for testing purposes"
tools: ["Read", "Write"]
skills: ["test-skill"]
---

# Test Agent

This is a test agent.
"""
    agent_file = cmat_test_env / ".claude/agents/test-agent.md"
    agent_file.write_text(agent_content)
    return agent_file


@pytest.fixture
def sample_task_data() -> dict:
    """Return sample task data for testing."""
    return {
        "id": "task_1234567890_12345",
        "title": "Test Task",
        "assigned_agent": "test-agent",
        "priority": "high",
        "status": "pending",
        "task_type": "analysis",
        "source_file": "test.md",
        "description": "A test task",
        "created": "2025-01-01T00:00:00Z",
        "auto_complete": True,
        "auto_chain": False,
        "metadata": {},
    }


@pytest.fixture
def sample_learning_data() -> dict:
    """Return sample learning data for testing."""
    return {
        "id": "learn_1234567890_12345",
        "summary": "Test learning summary",
        "content": "This is a test learning with more detailed content.",
        "tags": ["testing", "python"],
        "applies_to": ["implementation"],
        "source_type": "user_feedback",
        "source_task_id": None,
        "confidence": 0.8,
        "created": "2025-01-01T00:00:00Z",
    }