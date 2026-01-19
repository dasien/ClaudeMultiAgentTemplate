"""
Base service infrastructure for CMAT.

This module provides shared functionality for services that manage JSON file-based
data storage, standardizing path resolution, file I/O, and collection operations.
"""

import json
import inspect
from abc import abstractmethod
from pathlib import Path
from typing import TypeVar, Optional

from core.utils import find_project_root

T = TypeVar("T")


class JSONFileServiceMixin:
    """
    Mixin providing standardized JSON file I/O operations.

    This mixin handles:
    - Path initialization with project root detection
    - File existence management with defaults
    - Basic JSON read/write operations
    - Array-based collection management
    - Keyed collection management

    Services must implement _get_default_data() to provide their
    default JSON structure.

    Usage Examples:

    # Array-based collection (tools.json)
    class ToolsService(JSONFileServiceMixin):
        def __init__(self, data_dir: Optional[str] = None):
            self._init_data_path(data_dir, "tools.json")
            self._ensure_file_exists()

        def _get_default_data(self) -> dict:
            return {"claude_code_tools": [...]}

        def list_all(self) -> dict[str, Tool]:
            return self._read_collection(Tool, "claude_code_tools", "name")

    # Keyed collection (models.json)
    class ModelService(JSONFileServiceMixin):
        def __init__(self, data_dir: Optional[str] = None):
            self._init_data_path(data_dir, "models.json")
            self._ensure_file_exists()

        def _get_default_data(self) -> dict:
            return {
                "models": {...},
                "default_model": "claude-sonnet-4.5"
            }

        def list_all(self) -> dict[str, ClaudeModel]:
            return self._read_keyed_collection(ClaudeModel, "models")
    """

    def _init_data_path(
        self, data_dir: Optional[str | Path], filename: str, subdir: Optional[str] = None
    ) -> None:
        """
        Initialize data file path.

        Args:
            data_dir: Optional directory path. If None, uses find_project_root()
                      to locate .claude/data/
            filename: Name of the data file (e.g., "tools.json")
            subdir: Optional subdirectory within data_dir

        Sets:
            self.data_file: Path to the data file
        """
        if data_dir is None:
            project_root = find_project_root()
            if project_root:
                base_path = project_root / ".claude/data"
            else:
                base_path = Path(".claude/data")
        else:
            base_path = Path(data_dir)

        if subdir:
            base_path = base_path / subdir

        self.data_file = base_path / filename

    def _ensure_file_exists(self) -> None:
        """
        Ensure data file exists with default content.

        Creates parent directories and writes default data via
        _get_default_data() if file doesn't exist. Does nothing
        if file already exists.
        """
        if not self.data_file.exists():
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            default_data = self._get_default_data()
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=2)

    @abstractmethod
    def _get_default_data(self) -> dict:
        """
        Get default data structure for the JSON file.

        Must be implemented by services to provide their
        specific default structure.

        Returns:
            Dictionary with default data structure
        """
        pass

    def _read_json(self) -> dict:
        """
        Read and parse JSON file.

        Returns default data if file doesn't exist (graceful degradation).

        Returns:
            Parsed JSON data as dictionary
        """
        if not self.data_file.exists():
            return self._get_default_data()

        with open(self.data_file, encoding="utf-8") as f:
            return json.load(f)  # type: ignore[no-any-return]

    def _write_json(self, data: dict) -> None:
        """
        Write data to JSON file.

        Creates parent directories if needed.
        Uses indent=2 for readable formatting.
        Uses UTF-8 encoding explicitly.

        Args:
            data: Dictionary to write as JSON
        """
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _read_collection(
        self, model_class: type[T], collection_key: str, id_field: str = "id"
    ) -> dict[str, T]:
        """
        Read array-based collection from JSON file.

        For JSON like: {"tools": [{"name": "Read", ...}, ...]}

        Args:
            model_class: Class to instantiate (must have from_dict(data: dict))
            collection_key: Top-level key containing the array
            id_field: Field name to use as dictionary key

        Returns:
            Dictionary mapping id_field values to model instances
        """
        data = self._read_json()
        collection_data = data.get(collection_key, [])
        result: dict[str, T] = {}

        for item_data in collection_data:
            instance = model_class.from_dict(item_data)  # type: ignore[attr-defined]
            # Get the id value from the instance
            item_id = getattr(instance, id_field)
            result[item_id] = instance

        return result

    def _write_collection(
        self, collection: dict[str, T], collection_key: str, extra_fields: Optional[dict] = None
    ) -> None:
        """
        Write array-based collection to JSON file.

        Args:
            collection: Dictionary of model instances
            collection_key: Top-level key for the array
            extra_fields: Additional top-level fields to include
        """
        # Convert collection to array of dicts
        array_data = [item.to_dict() for item in collection.values()]  # type: ignore[attr-defined]

        # Build final data structure
        data = {collection_key: array_data}

        if extra_fields:
            data.update(extra_fields)

        self._write_json(data)

    def _read_keyed_collection(self, model_class: type[T], collection_key: str) -> dict[str, T]:
        """
        Read keyed collection from JSON file.

        For JSON like: {"models": {"id1": {...}, "id2": {...}}}

        Supports models with from_dict(id: str, data: dict) signature
        (like ClaudeModel) as well as standard from_dict(data: dict).

        Args:
            model_class: Class to instantiate
            collection_key: Top-level key containing the keyed object

        Returns:
            Dictionary mapping keys to model instances
        """
        data = self._read_json()
        collection_data = data.get(collection_key, {})
        result: dict[str, T] = {}

        # Check if from_dict takes 2 positional args (id + data)
        # Note: classmethod signatures don't include 'cls' parameter
        sig = inspect.signature(model_class.from_dict)  # type: ignore[attr-defined]
        params = list(sig.parameters.values())
        # If there are 2 or more params (id, data), it takes id as first param
        takes_id_param = len(params) >= 2

        for item_id, item_data in collection_data.items():
            if takes_id_param:
                # Model expects from_dict(id, data)
                instance = model_class.from_dict(item_id, item_data)  # type: ignore[attr-defined]
            else:
                # Model expects from_dict(data) with id in data
                item_data_with_id = {**item_data, "id": item_id}
                instance = model_class.from_dict(item_data_with_id)  # type: ignore[attr-defined]

            result[item_id] = instance

        return result

    def _write_keyed_collection(
        self, collection: dict[str, T], collection_key: str, extra_fields: Optional[dict] = None
    ) -> None:
        """
        Write keyed collection to JSON file.

        Args:
            collection: Dictionary of model instances
            collection_key: Top-level key for the keyed object
            extra_fields: Additional top-level fields to include
        """
        # Convert collection to keyed dict
        keyed_data = {
            item_id: item.to_dict()  # type: ignore[attr-defined]
            for item_id, item in collection.items()
        }

        # Build final data structure
        data = {collection_key: keyed_data}

        if extra_fields:
            data.update(extra_fields)

        self._write_json(data)
