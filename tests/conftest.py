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
    (temp_dir / ".claude/prompts").mkdir(parents=True)
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

    # Create minimal base.md for prompts
    base_content = """You are the **${agent}** agent. Your configuration and instructions are in: `${agent_config}`

## Task: ${task_description}

You are working on enhancement: **${enhancement_name}**

## Input

${input_instruction}

## Output Requirements

Create the following directory structure:

```
${enhancement_dir}/${agent}/
├── required_output/
│   └── ${required_output_filename}  (REQUIRED)
└── optional_output/                  (OPTIONAL)
    └── [any additional files]
```

### Required Output File

You **must** create: `${enhancement_dir}/${agent}/required_output/${required_output_filename}`

This file must include a metadata header:
```markdown
---
enhancement: ${enhancement_name}
agent: ${agent}
task_id: ${task_id}
timestamp: <ISO-8601-timestamp>
status: <your-completion-status>
---
```

### Optional Outputs

Place any additional supporting documents in: `${enhancement_dir}/${agent}/optional_output/`

## Completion Block

At the end of your response, you **must** output a completion block in this exact format:

```yaml
---
agent: ${agent}
task_id: ${task_id}
status: <STATUS>
skills_used: [list of skill names you applied, or empty array if none]
---
```

The `status` field must be one of the following:

${expected_statuses}

The `skills_used` field should list any specialized skills you applied from those available to you. If you didn't use any skills, use an empty array `[]`.

## Your Task

Read the agent configuration at `${agent_config}` for detailed instructions on your role and responsibilities, then complete the analysis task described above.
"""
    with open(temp_dir / ".claude/prompts/base.md", "w") as f:
        f.write(base_content)

    # Create minimal role files for testing
    role_files = {
        "analysis.md": "These might include:\n- Detailed analysis notes\n- Research findings\n- Alternative approaches considered\n- Risk assessments\n",
        "design.md": "These might include:\n- Architecture diagrams\n- API specifications\n- Data model designs\n- Technology research\n",
        "implementation.md": "These might include:\n- Implementation notes\n- Code change summaries\n- Refactoring documentation\n- Performance considerations\n",
        "testing.md": "These might include:\n- Detailed test results\n- Coverage reports\n- Performance test data\n- Bug reports\n",
        "documentation.md": "These might include:\n- User guide updates\n- API documentation updates\n- Additional examples\n- Tutorial content\n",
        "integration.md": "**Note**: Integration tasks may include additional metadata fields for tracking synchronization state.\n\nThese might include:\n- Integration logs\n- Sync reports\n- Error details\n",
    }
    for filename, content in role_files.items():
        with open(temp_dir / f".claude/prompts/{filename}", "w") as f:
            f.write(content)

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
        "created": "2025-01-01T00:00:00Z",
    }