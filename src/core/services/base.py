"""Base classes and mixins for services."""

import json
from abc import abstractmethod
from pathlib import Path
from typing import Any, Optional, TypeVar

from core.utils import find_project_root

T = TypeVar('T')


class JSONFileServiceMixin:
    """
    Mixin providing common JSON file I/O operations for services.

    Services that store data in JSON files can use this mixin to standardize
    file reading, writing, and initialization patterns.

    Usage:
        class MyService(JSONFileServiceMixin):
            def __init__(self, data_dir: Optional[str] = None):
                self._init_data_path(data_dir, "my_data.json")

            def _get_default_data(self) -> dict:
                return {"version": "1.0.0", "items": []}

            def _get_collection_key(self) -> str:
                return "items"
    """

    data_file: Path

    def _init_data_path(
        self,
        data_dir: Optional[str],
        filename: str,
        subdir: str = "data"
    ) -> None:
        """
        Initialize the data file path.

        Args:
            data_dir: Optional explicit data directory path
            filename: Name of the JSON file
            subdir: Subdirectory under .claude (default: "data")
        """
        if data_dir is not None:
            self.data_file = Path(data_dir) / filename
        else:
            project_root = find_project_root()
            if project_root:
                self.data_file = project_root / ".claude" / subdir / filename
            else:
                self.data_file = Path(".claude") / subdir / filename

    def _ensure_file_exists(self) -> None:
        """Ensure the data file exists with default structure."""
        if not self.data_file.exists():
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._write_json(self._get_default_data())

    @abstractmethod
    def _get_default_data(self) -> dict:
        """
        Return the default data structure for a new file.

        Override in subclass to provide service-specific defaults.

        Returns:
            Dictionary with default structure
        """
        pass

    def _read_json(self) -> dict:
        """
        Read and parse the JSON data file.

        Returns:
            Parsed JSON data as dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        if not self.data_file.exists():
            return self._get_default_data()

        with open(self.data_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write_json(self, data: dict) -> None:
        """
        Write data to the JSON file.

        Creates parent directories if they don't exist.

        Args:
            data: Dictionary to write as JSON
        """
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def _read_collection(
        self,
        model_class: type[T],
        collection_key: str,
        id_field: str = "id"
    ) -> dict[str, T]:
        """
        Read a collection of models from the JSON file.

        Args:
            model_class: Class with from_dict() method
            collection_key: Key in JSON containing the collection array
            id_field: Field name to use as dictionary key

        Returns:
            Dictionary mapping id_field values to model instances

        Example:
            tools = self._read_collection(Tool, "tools", "name")
        """
        data = self._read_json()
        collection: dict[str, Any] = {}

        for item_data in data.get(collection_key, []):
            model = model_class.from_dict(item_data)
            key = getattr(model, id_field)
            collection[key] = model

        return collection

    def _write_collection(
        self,
        collection: dict[str, T],
        collection_key: str,
        extra_fields: Optional[dict] = None
    ) -> None:
        """
        Write a collection of models to the JSON file.

        Args:
            collection: Dictionary of models
            collection_key: Key for the collection in output JSON
            extra_fields: Additional top-level fields (e.g., version)

        Example:
            self._write_collection(self._tools, "tools", {"version": "1.0.0"})
        """
        data = {
            collection_key: [model.to_dict() for model in collection.values()]
        }

        if extra_fields:
            data.update(extra_fields)

        self._write_json(data)

    def _read_keyed_collection(
        self,
        model_class: type[T],
        collection_key: str
    ) -> dict[str, T]:
        """
        Read a collection where items are stored as {id: data} pairs.

        Used for WorkflowTemplate, ClaudeModel patterns where ID is the key.

        Args:
            model_class: Class with from_dict(id, data) signature
            collection_key: Key in JSON containing the collection dict

        Returns:
            Dictionary mapping IDs to model instances

        Example:
            workflows = self._read_keyed_collection(WorkflowTemplate, "workflows")
        """
        data = self._read_json()
        collection: dict[str, Any] = {}

        for item_id, item_data in data.get(collection_key, {}).items():
            model = model_class.from_dict(item_id, item_data)
            collection[item_id] = model

        return collection

    def _write_keyed_collection(
        self,
        collection: dict[str, T],
        collection_key: str,
        extra_fields: Optional[dict] = None
    ) -> None:
        """
        Write a collection as {id: data} pairs.

        Args:
            collection: Dictionary of models (keyed by ID)
            collection_key: Key for the collection in output JSON
            extra_fields: Additional top-level fields

        Example:
            self._write_keyed_collection(self._workflows, "workflows", {"version": "1.0.0"})
        """
        data = {
            collection_key: {
                model_id: model.to_dict()
                for model_id, model in collection.items()
            }
        }

        if extra_fields:
            data.update(extra_fields)

        self._write_json(data)
