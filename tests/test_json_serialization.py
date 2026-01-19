"""
Comprehensive tests for JSON serialization methods added in Phase 2.

Tests cover:
- TaskMetadata JSON roundtrip serialization
- ModelPricing JSON roundtrip serialization
- StepTransition from_json with special signature
- Edge cases and error handling
"""

import json
import pytest

from src.core.models.task_metadata import TaskMetadata
from src.core.models.claude_model import ModelPricing
from src.core.models.step_transition import StepTransition


class TestTaskMetadataJSONSerialization:
    """Tests for TaskMetadata JSON serialization methods."""

    def test_to_json_creates_valid_json_string(self):
        """Test that to_json() produces valid JSON string."""
        metadata = TaskMetadata(github_issue="TEST-123")
        json_str = metadata.to_json()

        # Should be a string
        assert isinstance(json_str, str)

        # Should be valid JSON (parsing shouldn't raise)
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

    def test_to_json_includes_all_fields(self):
        """Test that to_json() includes all populated fields."""
        metadata = TaskMetadata(
            github_issue="ISSUE-123",
            workflow_name="test-workflow",
            cost_usd="1.50",
            learnings_retrieved=["learning-1", "learning-2"],
            learnings_created=["learning-3"]
        )
        json_str = metadata.to_json()
        parsed = json.loads(json_str)

        assert parsed["github_issue"] == "ISSUE-123"
        assert parsed["workflow_name"] == "test-workflow"
        assert parsed["cost_usd"] == "1.50"
        assert parsed["learnings_retrieved"] == ["learning-1", "learning-2"]
        assert parsed["learnings_created"] == ["learning-3"]

    def test_to_json_uses_2_space_indentation(self):
        """Test that JSON output is formatted with 2-space indentation."""
        metadata = TaskMetadata(github_issue="TEST-123")
        json_str = metadata.to_json()

        # Check for 2-space indentation pattern
        assert "\n  " in json_str

    def test_from_json_recreates_instance(self):
        """Test that from_json() correctly recreates instance."""
        json_str = '{"github_issue": "ISSUE-456", "workflow_name": "test"}'
        metadata = TaskMetadata.from_json(json_str)

        assert isinstance(metadata, TaskMetadata)
        assert metadata.github_issue == "ISSUE-456"
        assert metadata.workflow_name == "test"

    def test_json_roundtrip_preserves_all_data(self):
        """Test full roundtrip: instance -> JSON -> instance."""
        original = TaskMetadata(
            github_issue="ROUNDTRIP-789",
            workflow_name="roundtrip-test",
            cost_usd="2.50",
            learnings_retrieved=["lr-1", "lr-2"],
            learnings_created=["lc-1"]
        )

        # Serialize to JSON
        json_str = original.to_json()

        # Deserialize back
        restored = TaskMetadata.from_json(json_str)

        # Verify all fields match
        assert restored.github_issue == original.github_issue
        assert restored.workflow_name == original.workflow_name
        assert restored.cost_usd == original.cost_usd
        assert restored.learnings_retrieved == original.learnings_retrieved
        assert restored.learnings_created == original.learnings_created

    def test_from_json_with_minimal_fields(self):
        """Test from_json() with only required/default fields."""
        json_str = '{}'
        metadata = TaskMetadata.from_json(json_str)

        # Should create instance with defaults
        assert metadata.github_issue is None
        assert metadata.workflow_name is None
        assert metadata.cost_usd is None
        assert metadata.learnings_retrieved == []
        assert metadata.learnings_created == []

    def test_from_json_with_null_values(self):
        """Test from_json() handles null values correctly."""
        json_str = '{"github_issue": null, "workflow_name": null, "cost_usd": null}'
        metadata = TaskMetadata.from_json(json_str)

        assert metadata.github_issue is None
        assert metadata.workflow_name is None
        assert metadata.cost_usd is None

    def test_from_json_invalid_json_raises_error(self):
        """Test that invalid JSON raises appropriate error."""
        invalid_json = '{"github_issue": "TEST-123"'  # Missing closing brace

        with pytest.raises(json.JSONDecodeError):
            TaskMetadata.from_json(invalid_json)


class TestModelPricingJSONSerialization:
    """Tests for ModelPricing JSON serialization methods."""

    def test_to_json_creates_valid_json_string(self):
        """Test that to_json() produces valid JSON string."""
        pricing = ModelPricing(
            input=3.0,
            output=15.0,
            cache_write=3.75,
            cache_read=0.3
        )
        json_str = pricing.to_json()

        # Should be a string
        assert isinstance(json_str, str)

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

    def test_to_json_includes_all_fields(self):
        """Test that to_json() includes all fields with correct types."""
        pricing = ModelPricing(
            input=3.0,
            output=15.0,
            cache_write=3.75,
            cache_read=0.3,
            currency="USD",
            per_tokens=1000000
        )
        json_str = pricing.to_json()
        parsed = json.loads(json_str)

        # Verify numeric values
        assert parsed["input"] == 3.0
        assert parsed["output"] == 15.0
        assert parsed["cache_write"] == 3.75
        assert parsed["cache_read"] == 0.3

        # Verify string and int values
        assert parsed["currency"] == "USD"
        assert parsed["per_tokens"] == 1000000

    def test_to_json_uses_2_space_indentation(self):
        """Test that JSON output is formatted with 2-space indentation."""
        pricing = ModelPricing(input=1.0, output=2.0, cache_write=1.5, cache_read=0.1)
        json_str = pricing.to_json()

        # Check for 2-space indentation
        assert "\n  " in json_str

    def test_from_json_recreates_instance(self):
        """Test that from_json() correctly recreates instance."""
        json_str = '{"input": 5.0, "output": 10.0, "cache_write": 6.0, "cache_read": 1.0}'
        pricing = ModelPricing.from_json(json_str)

        assert isinstance(pricing, ModelPricing)
        assert pricing.input == 5.0
        assert pricing.output == 10.0
        assert pricing.cache_write == 6.0
        assert pricing.cache_read == 1.0

    def test_json_roundtrip_preserves_all_data(self):
        """Test full roundtrip: instance -> JSON -> instance."""
        original = ModelPricing(
            input=3.0,
            output=15.0,
            cache_write=3.75,
            cache_read=0.3,
            currency="EUR",
            per_tokens=500000
        )

        # Serialize to JSON
        json_str = original.to_json()

        # Deserialize back
        restored = ModelPricing.from_json(json_str)

        # Verify all fields match
        assert restored.input == original.input
        assert restored.output == original.output
        assert restored.cache_write == original.cache_write
        assert restored.cache_read == original.cache_read
        assert restored.currency == original.currency
        assert restored.per_tokens == original.per_tokens

    def test_from_json_with_defaults(self):
        """Test from_json() uses defaults for optional fields."""
        json_str = '{"input": 1.0, "output": 2.0, "cache_write": 1.5, "cache_read": 0.5}'
        pricing = ModelPricing.from_json(json_str)

        # Should use default values from from_dict()
        assert pricing.currency == "USD"
        assert pricing.per_tokens == 1000000

    def test_from_json_invalid_json_raises_error(self):
        """Test that invalid JSON raises appropriate error."""
        invalid_json = '{"input": 1.0, "output"'  # Truncated JSON

        with pytest.raises(json.JSONDecodeError):
            ModelPricing.from_json(invalid_json)

    def test_from_json_missing_required_field_raises_error(self):
        """Test that missing required field raises KeyError."""
        # Missing 'input' field which is required
        json_str = '{"output": 2.0, "cache_write": 1.5, "cache_read": 0.5}'

        with pytest.raises(KeyError):
            ModelPricing.from_json(json_str)


class TestStepTransitionJSONSerialization:
    """Tests for StepTransition from_json method (to_json already existed)."""

    def test_from_json_requires_name_parameter(self):
        """Test that from_json() correctly uses the name parameter."""
        json_str = '{"next_step": "implement", "auto_chain": true}'
        transition = StepTransition.from_json("READY_FOR_IMPLEMENTATION", json_str)

        assert isinstance(transition, StepTransition)
        assert transition.name == "READY_FOR_IMPLEMENTATION"
        assert transition.next_step == "implement"
        assert transition.auto_chain is True

    def test_from_json_preserves_all_fields(self):
        """Test that from_json() correctly recreates all fields."""
        json_str = '''
        {
            "next_step": "test",
            "auto_chain": true,
            "auto_start": false,
            "description": "Ready for testing"
        }
        '''
        transition = StepTransition.from_json("READY_FOR_TESTING", json_str)

        assert transition.name == "READY_FOR_TESTING"
        assert transition.next_step == "test"
        assert transition.auto_chain is True
        assert transition.auto_start is False
        assert transition.description == "Ready for testing"

    def test_from_json_with_minimal_fields(self):
        """Test from_json() with minimal required fields."""
        json_str = '{"next_step": null, "auto_chain": false}'
        transition = StepTransition.from_json("BLOCKED", json_str)

        assert transition.name == "BLOCKED"
        assert transition.next_step is None
        assert transition.auto_chain is False
        assert transition.auto_start is True  # default value
        assert transition.description is None  # optional field

    def test_json_roundtrip_preserves_data(self):
        """Test roundtrip using existing to_json() and new from_json()."""
        original = StepTransition(
            name="TEST_STATUS",
            next_step="next",
            auto_chain=True,
            auto_start=False,
            description="Test description"
        )

        # Serialize to JSON using existing to_json()
        # Note: to_json() wraps the dict in {name: data} format
        json_str = original.to_json()
        parsed = json.loads(json_str)

        # Extract the wrapped data (to_json includes the name as key)
        unwrapped_json = json.dumps(parsed["TEST_STATUS"])

        # Deserialize using from_json()
        restored = StepTransition.from_json("TEST_STATUS", unwrapped_json)

        # Verify all fields match
        assert restored.name == original.name
        assert restored.next_step == original.next_step
        assert restored.auto_chain == original.auto_chain
        assert restored.auto_start == original.auto_start
        assert restored.description == original.description

    def test_from_json_with_null_next_step(self):
        """Test from_json() handles null next_step (terminal status)."""
        json_str = '{"next_step": null, "auto_chain": false}'
        transition = StepTransition.from_json("COMPLETE", json_str)

        assert transition.next_step is None
        assert transition.auto_chain is False

    def test_from_json_invalid_json_raises_error(self):
        """Test that invalid JSON raises appropriate error."""
        invalid_json = '{"next_step": "test"'  # Missing closing brace

        with pytest.raises(json.JSONDecodeError):
            StepTransition.from_json("STATUS", invalid_json)

    def test_from_json_uses_defaults_for_missing_fields(self):
        """Test that missing optional fields use defaults."""
        # Only next_step provided, other fields should use defaults
        json_str = '{"next_step": "test"}'
        transition = StepTransition.from_json("STATUS", json_str)

        assert transition.next_step == "test"
        assert transition.auto_chain is True  # default
        assert transition.auto_start is True  # default
        assert transition.description is None  # optional


class TestJSONSerializationIntegration:
    """Integration tests for JSON serialization across models."""

    def test_all_models_produce_valid_json(self):
        """Test that all models produce valid, parseable JSON."""
        # TaskMetadata
        metadata = TaskMetadata(github_issue="TEST-123")
        metadata_json = metadata.to_json()
        assert json.loads(metadata_json)  # Should not raise

        # ModelPricing
        pricing = ModelPricing(input=1.0, output=2.0, cache_write=1.5, cache_read=0.5)
        pricing_json = pricing.to_json()
        assert json.loads(pricing_json)  # Should not raise

        # StepTransition
        transition = StepTransition(name="TEST", next_step="next", auto_chain=True)
        transition_json = transition.to_json()
        assert json.loads(transition_json)  # Should not raise

    def test_all_models_use_2_space_indentation(self):
        """Test that all models use consistent 2-space indentation."""
        # TaskMetadata
        metadata = TaskMetadata(github_issue="TEST-123")
        assert "\n  " in metadata.to_json()

        # ModelPricing
        pricing = ModelPricing(input=1.0, output=2.0, cache_write=1.5, cache_read=0.5)
        assert "\n  " in pricing.to_json()

        # StepTransition
        transition = StepTransition(name="TEST", next_step="next", auto_chain=True)
        assert "\n  " in transition.to_json()

    def test_delegation_to_dict_methods(self):
        """Test that JSON methods delegate to existing dict methods."""
        # TaskMetadata: JSON should match dict content
        metadata = TaskMetadata(github_issue="TEST-123", workflow_name="test")
        json_parsed = json.loads(metadata.to_json())
        dict_data = metadata.to_dict()
        assert json_parsed == dict_data

        # ModelPricing: JSON should match dict content
        pricing = ModelPricing(input=1.0, output=2.0, cache_write=1.5, cache_read=0.5)
        json_parsed = json.loads(pricing.to_json())
        dict_data = pricing.to_dict()
        assert json_parsed == dict_data
