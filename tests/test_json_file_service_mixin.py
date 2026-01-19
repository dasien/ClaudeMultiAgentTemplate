"""
Comprehensive tests for JSONFileServiceMixin (Phase 3).

Tests cover:
- Path initialization with project root detection
- File existence management with defaults
- Basic JSON read/write operations
- Array-based collection management
- Keyed collection management
- Error handling and edge cases
- Backwards compatibility with existing models
"""

import json
import pytest
from pathlib import Path
from dataclasses import dataclass

from src.core.services.base import JSONFileServiceMixin
from src.core.models import Tool, ClaudeModel, ModelPricing


# Test model classes

@dataclass
class SimpleModel:
    """Simple test model with standard from_dict signature."""
    id: str
    name: str
    value: int

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "value": self.value}

    @classmethod
    def from_dict(cls, data: dict) -> "SimpleModel":
        return cls(
            id=data["id"],
            name=data["name"],
            value=data["value"]
        )


@dataclass
class TwoParamModel:
    """Test model with from_dict(id, data) signature like ClaudeModel."""
    id: str
    name: str
    count: int

    def to_dict(self) -> dict:
        # ID is not included in the dict for keyed collections
        return {"name": self.name, "count": self.count}

    @classmethod
    def from_dict(cls, model_id: str, data: dict) -> "TwoParamModel":
        """Takes id as separate parameter."""
        return cls(
            id=model_id,
            name=data["name"],
            count=data["count"]
        )


# Concrete test service classes

class ArrayCollectionService(JSONFileServiceMixin):
    """Test service using array-based collection pattern."""

    def __init__(self, data_dir: str):
        self._init_data_path(data_dir, "array_test.json")
        self._ensure_file_exists()

    def _get_default_data(self) -> dict:
        return {"items": [], "metadata": {"version": "1.0"}}

    def list_all(self) -> dict[str, SimpleModel]:
        return self._read_collection(SimpleModel, "items", "id")

    def save_all(self, items: dict[str, SimpleModel]) -> None:
        extra = {"metadata": {"version": "1.0"}}
        self._write_collection(items, "items", extra)


class KeyedCollectionService(JSONFileServiceMixin):
    """Test service using keyed collection pattern."""

    def __init__(self, data_dir: str):
        self._init_data_path(data_dir, "keyed_test.json")
        self._ensure_file_exists()

    def _get_default_data(self) -> dict:
        return {"models": {}, "default_model": "test-1"}

    def list_all(self) -> dict[str, TwoParamModel]:
        return self._read_keyed_collection(TwoParamModel, "models")

    def save_all(self, models: dict[str, TwoParamModel]) -> None:
        extra = {"default_model": "test-1"}
        self._write_keyed_collection(models, "models", extra)


class PathTestService(JSONFileServiceMixin):
    """Test service for path initialization testing."""

    def __init__(self, data_dir: str | Path | None, subdir: str | None = None):
        self._init_data_path(data_dir, "path_test.json", subdir)

    def _get_default_data(self) -> dict:
        return {"test": "data"}


class TestPathInitialization:
    """Tests for _init_data_path method."""

    def test_init_with_explicit_dir(self, temp_dir):
        """Test path initialization with explicit directory."""
        service = PathTestService(str(temp_dir))
        assert service.data_file == temp_dir / "path_test.json"

    def test_init_with_path_object(self, temp_dir):
        """Test path initialization with Path object."""
        service = PathTestService(temp_dir)
        assert service.data_file == temp_dir / "path_test.json"

    def test_init_with_subdirectory(self, temp_dir):
        """Test path initialization with subdirectory."""
        service = PathTestService(str(temp_dir), subdir="subdir")
        assert service.data_file == temp_dir / "subdir" / "path_test.json"

    def test_init_with_none_uses_project_root(self):
        """Test that None data_dir uses find_project_root()."""
        # When None is passed, should use project root detection
        # This test verifies the logic works without mocking
        service = PathTestService(None)

        # Should create a path under .claude/data
        assert ".claude/data" in str(service.data_file)
        assert service.data_file.name == "path_test.json"


class TestFileExistenceManagement:
    """Tests for _ensure_file_exists and _get_default_data."""

    def test_ensure_file_exists_creates_file(self, temp_dir):
        """Test that _ensure_file_exists creates file with default data."""
        service = ArrayCollectionService(str(temp_dir))

        assert service.data_file.exists()
        with open(service.data_file) as f:
            data = json.load(f)
        assert data == {"items": [], "metadata": {"version": "1.0"}}

    def test_ensure_file_exists_creates_parent_dirs(self, temp_dir):
        """Test that parent directories are created if needed."""
        nested_dir = temp_dir / "a" / "b" / "c"
        service = PathTestService(nested_dir)
        service._ensure_file_exists()

        assert service.data_file.exists()
        assert service.data_file.parent.exists()

    def test_ensure_file_exists_does_not_overwrite(self, temp_dir):
        """Test that existing files are not overwritten."""
        service = ArrayCollectionService(str(temp_dir))

        # Write custom data
        custom_data = {"items": [{"id": "1", "name": "test", "value": 42}]}
        with open(service.data_file, "w") as f:
            json.dump(custom_data, f)

        # Call ensure again - should not overwrite
        service._ensure_file_exists()

        with open(service.data_file) as f:
            data = json.load(f)
        assert data == custom_data


class TestBasicJSONOperations:
    """Tests for _read_json and _write_json methods."""

    def test_read_json_returns_data(self, temp_dir):
        """Test that _read_json returns parsed JSON data."""
        service = ArrayCollectionService(str(temp_dir))

        data = service._read_json()
        assert isinstance(data, dict)
        assert "items" in data
        assert "metadata" in data

    def test_read_json_graceful_degradation(self, temp_dir):
        """Test that _read_json returns default data if file missing."""
        service = ArrayCollectionService(str(temp_dir))
        service.data_file.unlink()  # Remove file

        data = service._read_json()
        assert data == {"items": [], "metadata": {"version": "1.0"}}

    def test_write_json_creates_file(self, temp_dir):
        """Test that _write_json creates file with correct data."""
        service = PathTestService(temp_dir)
        test_data = {"key": "value", "number": 42, "nested": {"a": 1}}

        service._write_json(test_data)

        assert service.data_file.exists()
        with open(service.data_file) as f:
            data = json.load(f)
        assert data == test_data

    def test_write_json_uses_utf8_encoding(self, temp_dir):
        """Test that _write_json uses UTF-8 encoding for unicode."""
        service = PathTestService(temp_dir)
        unicode_data = {"text": "Hello 世界 🌍", "emoji": "✅"}

        service._write_json(unicode_data)

        # Read with explicit UTF-8
        with open(service.data_file, encoding="utf-8") as f:
            data = json.load(f)
        assert data["text"] == "Hello 世界 🌍"
        assert data["emoji"] == "✅"

    def test_write_json_uses_indentation(self, temp_dir):
        """Test that _write_json formats with indentation."""
        service = PathTestService(temp_dir)
        service._write_json({"a": 1, "b": 2})

        content = service.data_file.read_text()
        assert "\n  " in content  # 2-space indentation

    def test_write_json_creates_parent_dirs(self, temp_dir):
        """Test that _write_json creates parent directories if needed."""
        nested_path = temp_dir / "deep" / "nested" / "path"
        service = PathTestService(nested_path)

        service._write_json({"test": "data"})

        assert service.data_file.exists()
        assert service.data_file.parent.exists()


class TestArrayCollectionManagement:
    """Tests for _read_collection and _write_collection methods."""

    def test_read_collection_empty(self, temp_dir):
        """Test reading empty array collection."""
        service = ArrayCollectionService(str(temp_dir))
        items = service.list_all()

        assert isinstance(items, dict)
        assert len(items) == 0

    def test_read_collection_with_items(self, temp_dir):
        """Test reading array collection with items."""
        service = ArrayCollectionService(str(temp_dir))

        # Write test data
        test_data = {
            "items": [
                {"id": "item-1", "name": "First", "value": 10},
                {"id": "item-2", "name": "Second", "value": 20},
            ],
            "metadata": {"version": "1.0"}
        }
        with open(service.data_file, "w") as f:
            json.dump(test_data, f)

        # Read collection
        items = service.list_all()

        assert len(items) == 2
        assert "item-1" in items
        assert "item-2" in items
        assert items["item-1"].name == "First"
        assert items["item-1"].value == 10
        assert items["item-2"].name == "Second"
        assert items["item-2"].value == 20

    def test_read_collection_custom_id_field(self, temp_dir):
        """Test reading collection with custom ID field."""
        service = PathTestService(temp_dir)
        service._ensure_file_exists()

        # Write data with 'name' as ID field
        test_data = {
            "tools": [
                {"name": "Read", "display_name": "Read Files", "description": "Read files"},
                {"name": "Write", "display_name": "Write Files", "description": "Write files"},
            ]
        }
        service._write_json(test_data)

        # Read using 'name' as id_field
        tools = service._read_collection(Tool, "tools", "name")

        assert len(tools) == 2
        assert "Read" in tools
        assert "Write" in tools
        assert tools["Read"].description == "Read files"

    def test_write_collection_creates_array(self, temp_dir):
        """Test writing collection creates array structure."""
        service = ArrayCollectionService(str(temp_dir))

        items = {
            "item-1": SimpleModel("item-1", "First", 10),
            "item-2": SimpleModel("item-2", "Second", 20),
        }
        service.save_all(items)

        with open(service.data_file) as f:
            data = json.load(f)

        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 2
        assert data["metadata"]["version"] == "1.0"

    def test_write_collection_preserves_extra_fields(self, temp_dir):
        """Test that extra_fields are preserved in output."""
        service = ArrayCollectionService(str(temp_dir))

        items = {"item-1": SimpleModel("item-1", "Test", 42)}
        service.save_all(items)

        with open(service.data_file) as f:
            data = json.load(f)

        assert "metadata" in data
        assert data["metadata"]["version"] == "1.0"

    def test_collection_roundtrip(self, temp_dir):
        """Test full roundtrip: write -> read -> verify."""
        service = ArrayCollectionService(str(temp_dir))

        # Create items
        original_items = {
            "a": SimpleModel("a", "Alpha", 1),
            "b": SimpleModel("b", "Beta", 2),
            "c": SimpleModel("c", "Gamma", 3),
        }

        # Write
        service.save_all(original_items)

        # Read back
        restored_items = service.list_all()

        # Verify
        assert len(restored_items) == 3
        for key in original_items:
            assert key in restored_items
            assert restored_items[key].id == original_items[key].id
            assert restored_items[key].name == original_items[key].name
            assert restored_items[key].value == original_items[key].value


class TestKeyedCollectionManagement:
    """Tests for _read_keyed_collection and _write_keyed_collection methods."""

    def test_read_keyed_collection_empty(self, temp_dir):
        """Test reading empty keyed collection."""
        service = KeyedCollectionService(str(temp_dir))
        models = service.list_all()

        assert isinstance(models, dict)
        assert len(models) == 0

    def test_read_keyed_collection_with_items(self, temp_dir):
        """Test reading keyed collection with items."""
        service = KeyedCollectionService(str(temp_dir))

        # Write test data
        test_data = {
            "models": {
                "model-1": {"name": "First Model", "count": 10},
                "model-2": {"name": "Second Model", "count": 20},
            },
            "default_model": "model-1"
        }
        with open(service.data_file, "w") as f:
            json.dump(test_data, f)

        # Read collection
        models = service.list_all()

        assert len(models) == 2
        assert "model-1" in models
        assert "model-2" in models
        assert models["model-1"].id == "model-1"
        assert models["model-1"].name == "First Model"
        assert models["model-1"].count == 10
        assert models["model-2"].id == "model-2"

    def test_read_keyed_collection_signature_detection(self, temp_dir):
        """Test that signature introspection correctly detects two-param models."""
        service = KeyedCollectionService(str(temp_dir))

        # Write data
        test_data = {
            "models": {
                "test-id": {"name": "Test", "count": 5}
            }
        }
        with open(service.data_file, "w") as f:
            json.dump(test_data, f)

        # Read - should use from_dict(id, data) signature
        models = service.list_all()

        assert "test-id" in models
        assert models["test-id"].id == "test-id"
        assert models["test-id"].name == "Test"

    def test_read_keyed_collection_with_standard_model(self, temp_dir):
        """Test keyed collection with standard from_dict(data) signature."""
        service = PathTestService(temp_dir)
        service._ensure_file_exists()

        # Write data with simple model
        test_data = {
            "items": {
                "id-1": {"id": "id-1", "name": "Item 1", "value": 100},
                "id-2": {"id": "id-2", "name": "Item 2", "value": 200},
            }
        }
        service._write_json(test_data)

        # Read with standard model (from_dict expects id in data)
        items = service._read_keyed_collection(SimpleModel, "items")

        assert len(items) == 2
        assert items["id-1"].name == "Item 1"
        assert items["id-2"].value == 200

    def test_write_keyed_collection_creates_keyed_object(self, temp_dir):
        """Test writing keyed collection creates keyed object structure."""
        service = KeyedCollectionService(str(temp_dir))

        models = {
            "model-1": TwoParamModel("model-1", "First", 10),
            "model-2": TwoParamModel("model-2", "Second", 20),
        }
        service.save_all(models)

        with open(service.data_file) as f:
            data = json.load(f)

        assert "models" in data
        assert isinstance(data["models"], dict)
        assert "model-1" in data["models"]
        assert "model-2" in data["models"]
        assert data["default_model"] == "test-1"

    def test_write_keyed_collection_preserves_extra_fields(self, temp_dir):
        """Test that extra_fields are preserved in keyed output."""
        service = KeyedCollectionService(str(temp_dir))

        models = {"m1": TwoParamModel("m1", "Test", 42)}
        service.save_all(models)

        with open(service.data_file) as f:
            data = json.load(f)

        assert "default_model" in data
        assert data["default_model"] == "test-1"

    def test_keyed_collection_roundtrip(self, temp_dir):
        """Test full roundtrip: write -> read -> verify."""
        service = KeyedCollectionService(str(temp_dir))

        # Create models
        original_models = {
            "alpha": TwoParamModel("alpha", "Alpha Model", 100),
            "beta": TwoParamModel("beta", "Beta Model", 200),
            "gamma": TwoParamModel("gamma", "Gamma Model", 300),
        }

        # Write
        service.save_all(original_models)

        # Read back
        restored_models = service.list_all()

        # Verify
        assert len(restored_models) == 3
        for key in original_models:
            assert key in restored_models
            assert restored_models[key].id == original_models[key].id
            assert restored_models[key].name == original_models[key].name
            assert restored_models[key].count == original_models[key].count


class TestRealWorldCompatibility:
    """Tests using actual CMAT models to verify compatibility."""

    def test_with_tool_model(self, cmat_test_env):
        """Test array collection with real Tool model."""
        service = PathTestService(str(cmat_test_env))
        service._ensure_file_exists()

        # Create tools using real Tool model
        tools_data = {
            "tools": [
                {
                    "name": "Read",
                    "display_name": "Read Files",
                    "description": "Read file contents",
                },
                {
                    "name": "Write",
                    "display_name": "Write Files",
                    "description": "Write file contents",
                },
            ]
        }
        service._write_json(tools_data)

        # Read using real Tool model
        tools = service._read_collection(Tool, "tools", "name")

        assert len(tools) == 2
        assert isinstance(tools["Read"], Tool)
        assert tools["Read"].display_name == "Read Files"
        assert tools["Write"].description == "Write file contents"

    def test_with_claude_model(self, cmat_test_env):
        """Test keyed collection with real ClaudeModel (two-param signature)."""
        service = PathTestService(str(cmat_test_env))
        service._ensure_file_exists()

        # Create model data
        models_data = {
            "models": {
                "sonnet-4.5": {
                    "pattern": "*sonnet-4-5*",
                    "name": "Claude Sonnet 4.5",
                    "description": "Balanced model",
                    "max_tokens": 200000,
                    "pricing": {
                        "input": 3.0,
                        "output": 15.0,
                        "cache_write": 3.75,
                        "cache_read": 0.3,
                        "currency": "USD",
                        "per_tokens": 1000000,
                    },
                }
            }
        }
        service._write_json(models_data)

        # Read using real ClaudeModel
        models = service._read_keyed_collection(ClaudeModel, "models")

        assert len(models) == 1
        assert isinstance(models["sonnet-4.5"], ClaudeModel)
        assert models["sonnet-4.5"].id == "sonnet-4.5"
        assert models["sonnet-4.5"].name == "Claude Sonnet 4.5"
        assert models["sonnet-4.5"].max_tokens == 200000
        assert isinstance(models["sonnet-4.5"].pricing, ModelPricing)

    def test_tool_roundtrip(self, cmat_test_env):
        """Test complete roundtrip with Tool model."""
        service = PathTestService(str(cmat_test_env))
        service._ensure_file_exists()

        # Create tools
        original_tools = {
            "Read": Tool(
                name="Read",
                display_name="Read Files",
                description="Read file contents"
            ),
            "Bash": Tool(
                name="Bash",
                display_name="Execute Shell",
                description="Run shell commands"
            ),
        }

        # Write
        service._write_collection(original_tools, "tools")

        # Read back
        restored_tools = service._read_collection(Tool, "tools", "name")

        # Verify
        assert len(restored_tools) == 2
        assert restored_tools["Read"].display_name == "Read Files"
        assert restored_tools["Bash"].description == "Run shell commands"


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_read_collection_missing_key(self, temp_dir):
        """Test reading collection when key doesn't exist."""
        service = PathTestService(temp_dir)
        service._ensure_file_exists()

        # Write data without expected key
        service._write_json({"other_key": []})

        # Read with missing key - should return empty dict
        items = service._read_collection(SimpleModel, "items", "id")
        assert items == {}

    def test_read_keyed_collection_missing_key(self, temp_dir):
        """Test reading keyed collection when key doesn't exist."""
        service = PathTestService(temp_dir)
        service._ensure_file_exists()

        # Write data without expected key
        service._write_json({"other_key": {}})

        # Read with missing key - should return empty dict
        models = service._read_keyed_collection(TwoParamModel, "models")
        assert models == {}

    def test_write_json_with_empty_dict(self, temp_dir):
        """Test writing empty dictionary."""
        service = PathTestService(temp_dir)
        service._write_json({})

        with open(service.data_file) as f:
            data = json.load(f)
        assert data == {}

    def test_write_collection_empty(self, temp_dir):
        """Test writing empty collection."""
        service = ArrayCollectionService(str(temp_dir))
        service.save_all({})

        with open(service.data_file) as f:
            data = json.load(f)

        assert data["items"] == []
        assert "metadata" in data

    def test_write_keyed_collection_empty(self, temp_dir):
        """Test writing empty keyed collection."""
        service = KeyedCollectionService(str(temp_dir))
        service.save_all({})

        with open(service.data_file) as f:
            data = json.load(f)

        assert data["models"] == {}
        assert "default_model" in data


class TestBackwardsCompatibility:
    """Tests ensuring backwards compatibility with existing services."""

    def test_tools_service_pattern(self, cmat_test_env):
        """Test pattern used by ToolsService."""
        # Simulate ToolsService usage pattern
        service = PathTestService(str(cmat_test_env / ".claude/data"))
        service.data_file = service.data_file.parent / "tools.json"

        # Read existing tools.json from fixture
        tools = service._read_collection(Tool, "claude_code_tools", "name")

        # Should read the fixture data correctly
        assert len(tools) == 3
        assert "Read" in tools
        assert "Write" in tools
        assert "Bash" in tools

    def test_model_service_pattern(self, cmat_test_env):
        """Test pattern used by ModelService."""
        # Simulate ModelService usage pattern
        service = PathTestService(str(cmat_test_env / ".claude/data"))
        service.data_file = service.data_file.parent / "models.json"

        # Read existing models.json from fixture
        models = service._read_keyed_collection(ClaudeModel, "models")

        # Should read the fixture data correctly
        assert len(models) == 1
        assert "claude-sonnet-4.5" in models
        assert models["claude-sonnet-4.5"].name == "Claude Sonnet 4.5"

        # Verify extra fields preserved
        full_data = service._read_json()
        assert full_data["default_model"] == "claude-sonnet-4.5"
        assert "metadata" in full_data
