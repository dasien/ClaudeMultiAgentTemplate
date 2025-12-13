"""Tests for TaskService."""

import pytest
from pathlib import Path

from cmat.services.task_service import TaskService, ExecutionResult


class TestTaskServiceTemplates:
    """Tests for template loading and prompt building."""

    @pytest.fixture
    def task_service(self, tmp_path):
        """Create TaskService with test templates."""
        # Create a minimal templates file
        templates_file = tmp_path / "templates.md"
        templates_file.write_text("""# Task Prompt Defaults

# ANALYSIS_TEMPLATE

You are the **${agent}** agent.

## Task: ${task_description}

Enhancement: ${enhancement_name}

${input_instruction}

Output to: ${enhancement_dir}/${agent}/required_output/${required_output_filename}

Task ID: ${task_id}

Expected statuses: ${expected_statuses}

===END_TEMPLATE===

# IMPLEMENTATION_TEMPLATE

You are ${agent} implementing: ${task_description}

===END_TEMPLATE===
""")
        return TaskService(
            templates_file=str(templates_file),
            agents_dir=str(tmp_path / "agents"),
            logs_dir=str(tmp_path / "logs"),
        )

    def test_load_templates(self, task_service):
        """Test that templates are loaded correctly."""
        templates = task_service._load_templates()

        assert "analysis" in templates
        assert "implementation" in templates
        assert "${agent}" in templates["analysis"]

    def test_get_template(self, task_service):
        """Test getting a specific template."""
        template = task_service.get_template("analysis")
        assert template is not None
        assert "${agent}" in template

    def test_get_nonexistent_template(self, task_service):
        """Test getting a template that doesn't exist."""
        template = task_service.get_template("nonexistent")
        assert template is None

    def test_build_prompt_substitutions(self, task_service):
        """Test that all variables are substituted in prompt."""
        prompt = task_service.build_prompt(
            agent_name="architect",
            task_type="analysis",
            task_id="task_123",
            task_description="Analyze the feature",
            source_file="requirements.md",
            enhancement_name="new-feature",
            enhancement_dir="enhancements/new-feature",
            required_output_filename="analysis.md",
            expected_statuses="- READY_FOR_DEVELOPMENT",
        )

        assert prompt is not None
        assert "architect" in prompt
        assert "Analyze the feature" in prompt
        assert "new-feature" in prompt
        assert "task_123" in prompt
        assert "READY_FOR_DEVELOPMENT" in prompt

        # Verify no unsubstituted variables remain
        assert "${" not in prompt

    def test_build_prompt_invalid_type(self, task_service):
        """Test building prompt with invalid task type."""
        prompt = task_service.build_prompt(
            agent_name="architect",
            task_type="invalid_type",
            task_id="task_123",
            task_description="Test",
        )
        assert prompt is None


class TestTaskServiceInputInstruction:
    """Tests for input instruction building."""

    @pytest.fixture
    def task_service(self, tmp_path):
        """Create TaskService."""
        templates_file = tmp_path / "templates.md"
        templates_file.write_text("""# ANALYSIS_TEMPLATE
${input_instruction}
===END_TEMPLATE===
""")
        return TaskService(templates_file=str(templates_file))

    def test_input_instruction_no_file(self, task_service):
        """Test input instruction when no source file."""
        instruction = task_service._build_input_instruction(None)
        assert "task description" in instruction.lower()

    def test_input_instruction_null_string(self, task_service):
        """Test input instruction with 'null' string."""
        instruction = task_service._build_input_instruction("null")
        assert "task description" in instruction.lower()

    def test_input_instruction_file(self, task_service, tmp_path):
        """Test input instruction for a file."""
        test_file = tmp_path / "input.md"
        test_file.write_text("test content")

        instruction = task_service._build_input_instruction(str(test_file))
        assert "Read and process this file" in instruction

    def test_input_instruction_directory(self, task_service, tmp_path):
        """Test input instruction for a directory."""
        test_dir = tmp_path / "inputs"
        test_dir.mkdir()

        instruction = task_service._build_input_instruction(str(test_dir))
        assert "directory" in instruction.lower()


class TestTaskServiceStatusExtraction:
    """Tests for status extraction from output."""

    @pytest.fixture
    def task_service(self):
        """Create TaskService."""
        return TaskService()

    def test_extract_ready_for_status(self, task_service):
        """Test extracting READY_FOR_* status."""
        output = """
        Analysis complete.

        READY_FOR_DEVELOPMENT
        """
        status = task_service.extract_status(output)
        assert status == "READY_FOR_DEVELOPMENT"

    def test_extract_complete_status(self, task_service):
        """Test extracting *_COMPLETE status."""
        output = """
        Implementation finished.

        IMPLEMENTATION_COMPLETE
        """
        status = task_service.extract_status(output)
        assert status == "IMPLEMENTATION_COMPLETE"

    def test_extract_blocked_status(self, task_service):
        """Test extracting BLOCKED: status."""
        output = """
        Cannot proceed.

        BLOCKED: Missing API credentials
        """
        status = task_service.extract_status(output)
        assert status.startswith("BLOCKED:")
        assert "credentials" in status

    def test_extract_needs_clarification(self, task_service):
        """Test extracting NEEDS_CLARIFICATION status."""
        output = """
        NEEDS_CLARIFICATION: What database should we use?
        """
        status = task_service.extract_status(output)
        assert status.startswith("NEEDS_CLARIFICATION:")

    def test_extract_last_status(self, task_service):
        """Test that last status is returned when multiple present."""
        output = """
        First attempt: BLOCKED: Initial issue

        After fix: READY_FOR_TESTING
        """
        status = task_service.extract_status(output)
        assert status == "READY_FOR_TESTING"

    def test_extract_no_status(self, task_service):
        """Test when no status pattern found."""
        output = """
        Just some regular output without a status.
        """
        status = task_service.extract_status(output)
        assert status is None

    def test_extract_status_from_long_output(self, task_service):
        """Test status extraction from very long output."""
        # Status should be found even in long output (checks last 5000 chars)
        output = "x" * 10000 + "\n\nREADY_FOR_REVIEW\n"
        status = task_service.extract_status(output)
        assert status == "READY_FOR_REVIEW"


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_execution_result_creation(self):
        """Test creating an ExecutionResult."""
        result = ExecutionResult(
            success=True,
            status="READY_FOR_TESTING",
            exit_code=0,
            output_dir="/path/to/output",
            log_file="/path/to/log",
            duration_seconds=120,
            pid=12345,
        )

        assert result.success is True
        assert result.status == "READY_FOR_TESTING"
        assert result.exit_code == 0
        assert result.pid == 12345

    def test_execution_result_default_pid(self):
        """Test ExecutionResult with default pid."""
        result = ExecutionResult(
            success=False,
            status=None,
            exit_code=1,
            output_dir="/path",
            log_file="/log",
            duration_seconds=0,
        )

        assert result.pid is None
