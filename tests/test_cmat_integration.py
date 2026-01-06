"""
Integration tests for CMAT interface.

Tests that the UI's cmat_interface correctly calls CMAT v8.2+ services
and handles method signatures, return types, and data transformations.
"""

import pytest
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from ui.utils.cmat_interface import CMATInterface


@pytest.fixture
def cmat_project_path():
    """Path to CMAT project for testing."""
    # Adjust this path as needed
    return Path(__file__).parent.parent.parent / "ClaudeMultiAgentTemplate"


@pytest.fixture
def cmat_interface(cmat_project_path):
    """Create CMATInterface instance for testing."""
    if not cmat_project_path.exists():
        pytest.skip(f"CMAT project not found at {cmat_project_path}")
    return CMATInterface(cmat_project_path)


class TestQueueOperations:
    """Test queue service operations."""

    def test_add_task_with_model(self, cmat_interface):
        """Test that add_task accepts model parameter."""
        # This shouldn't raise an exception
        task_id = cmat_interface.add_task(
            title="[TEST] Task with model",
            agent="requirements-analyst",
            priority="normal",
            task_type="analysis",
            source_file="test.md",
            description="Test description",
            model="claude-sonnet-4-20250514"
        )
        assert task_id is not None

        # Clean up: delete the test task
        cmat_interface.clear_tasks([task_id])

    def test_add_task_without_model(self, cmat_interface):
        """Test that add_task works without model parameter (uses default)."""
        task_id = cmat_interface.add_task(
            title="[TEST] Task without model",
            agent="requirements-analyst",
            priority="normal",
            task_type="analysis",
            source_file="test.md",
            description="Test description"
        )
        assert task_id is not None

        # Clean up: delete the test task
        cmat_interface.clear_tasks([task_id])


class TestWorkflowOperations:
    """Test workflow service operations."""

    def test_get_workflow_templates(self, cmat_interface):
        """Test getting workflow templates."""
        templates = cmat_interface.get_workflow_templates()
        assert isinstance(templates, list)

    def test_get_workflow_template(self, cmat_interface):
        """Test getting single workflow template."""
        templates = cmat_interface.get_workflow_templates()
        if templates:
            template = cmat_interface.get_workflow_template(templates[0].id)
            assert template is not None
            assert hasattr(template, 'steps')
            assert hasattr(template, 'name')

    def test_workflow_step_index_type_conversion(self, cmat_interface):
        """Test that workflow step index handles string to int conversion."""
        templates = cmat_interface.get_workflow_templates()
        if templates:
            # Pass step_index as string (as it comes from metadata)
            details = cmat_interface.get_workflow_step_details(
                templates[0].id, "0"
            )
            # Should not raise TypeError


class TestAgentOperations:
    """Test agent service operations."""

    def test_get_agent_list(self, cmat_interface):
        """Test getting agent list."""
        agents = cmat_interface.get_agent_list()
        assert isinstance(agents, dict)
        # May be empty if no agents directory exists in test project

    def test_get_agent_skills(self, cmat_interface):
        """Test getting agent skills."""
        agents = cmat_interface.get_agent_list()
        if agents:
            first_agent = list(agents.keys())[0]
            skills = cmat_interface.get_agent_skills(first_agent)
            assert isinstance(skills, list)


class TestSkillsOperations:
    """Test skills service operations."""

    def test_get_skills_list(self, cmat_interface):
        """Test getting skills list."""
        skills = cmat_interface.get_skills_list()
        assert isinstance(skills, dict)
        assert 'skills' in skills

    def test_get_skills_prompt(self, cmat_interface):
        """Test building skills prompt."""
        agents = cmat_interface.get_agent_list()
        if agents:
            first_agent = list(agents.keys())[0]
            prompt = cmat_interface.get_skills_prompt(first_agent)
            # Should return string or None, not raise exception
            assert prompt is None or isinstance(prompt, str)

    def test_skills_prompt_uses_correct_method(self, cmat_interface):
        """Test that get_skills_prompt calls build_skills_prompt (not build_prompt)."""
        # This test verifies the method name fix
        agents = cmat_interface.get_agent_list()
        if agents:
            first_agent = list(agents.keys())[0]
            skills = cmat_interface.get_agent_skills(first_agent)
            if skills:
                # Should not raise AttributeError about 'build_prompt'
                prompt = cmat_interface.get_skills_prompt(first_agent)
                assert prompt is not None


class TestModelOperations:
    """Test model service operations."""

    def test_get_models_list(self, cmat_interface):
        """Test getting models list."""
        models = cmat_interface.models.list_all()
        assert isinstance(models, list)

    def test_get_default_model(self, cmat_interface):
        """Test getting default model."""
        default = cmat_interface.models.get_default()
        assert default is not None
        assert hasattr(default, 'id')
        assert hasattr(default, 'name')

    def test_get_model_by_id(self, cmat_interface):
        """Test getting model by ID."""
        models = cmat_interface.models.list_all()
        if models:
            model = cmat_interface.models.get(models[0].id)
            assert model is not None


class TestDataTransformations:
    """Test data transformations between CMAT and UI models."""

    def test_workflow_template_field_mapping(self, cmat_interface):
        """Test that workflow templates have expected fields."""
        templates = cmat_interface.get_workflow_templates()
        if templates:
            template = templates[0]
            # Core model uses 'id' (not 'slug')
            assert hasattr(template, 'id')
            assert hasattr(template, 'name')
            assert hasattr(template, 'steps')

            # Steps should have 'input' (mapped from CMAT's 'input')
            if template.steps:
                step = template.steps[0]
                assert hasattr(step, 'input')
                assert hasattr(step, 'agent')
                assert hasattr(step, 'required_output')

    def test_task_metadata_format(self, cmat_interface):
        """Test that task metadata is properly formatted."""
        # Create a task with model
        task_id = cmat_interface.add_task(
            title="[TEST] Metadata validation",
            agent="requirements-analyst",
            priority="normal",
            task_type="analysis",
            source_file="test.md",
            description="Test",
            model="claude-sonnet-4-20250514"
        )

        try:
            # Get the task back
            state = cmat_interface.get_queue_state()
            tasks = state.pending_tasks + state.active_workflows + state.completed_tasks
            task = next((t for t in tasks if t.id == task_id), None)

            if task and task.metadata:
                # Should have requested_model in metadata (TaskMetadata object)
                assert hasattr(task.metadata, 'requested_model')
                assert task.metadata.requested_model == "claude-sonnet-4-20250514"
        finally:
            # Clean up: delete the test task
            cmat_interface.clear_tasks([task_id])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
