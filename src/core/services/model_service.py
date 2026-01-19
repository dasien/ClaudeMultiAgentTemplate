"""
ModelService for managing Claude models and extracting costs from transcripts.

This service handles:
- CRUD operations for Claude model definitions in models.json
- Looking up models by pattern matching
- Parsing transcript JSONL files to extract token usage
- Calculating costs using model pricing
- Storing cost data in task metadata
"""

import json
from pathlib import Path
from typing import Optional

from core.models.claude_model import ClaudeModel, ModelPricing
from core.services.base import JSONFileServiceMixin


class ModelService(JSONFileServiceMixin):
    """
    Service for managing Claude models and calculating costs.

    Provides CRUD operations for model definitions and cost extraction
    from Claude transcripts.
    """

    COLLECTION_KEY = "models"

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize ModelService.

        Args:
            data_dir: Path to data directory containing models.json.
                     If None, uses default location via find_project_root().
        """
        self._init_data_path(data_dir, "models.json")
        self._ensure_file_exists()

    def _get_default_data(self) -> dict:
        """Get default models data structure."""
        return {
            self.COLLECTION_KEY: {
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
                "last_updated": "",
                "pricing_source": "https://www.anthropic.com/pricing",
            },
        }

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def list_all(self) -> list[ClaudeModel]:
        """
        List all available models.

        Returns:
            List of ClaudeModel objects
        """
        collection = self._read_keyed_collection(ClaudeModel, self.COLLECTION_KEY)
        return list(collection.values())

    def get(self, model_id: str) -> Optional[ClaudeModel]:
        """
        Get a model by its ID.

        Args:
            model_id: The model ID (e.g., "claude-sonnet-4.5")

        Returns:
            ClaudeModel if found, None otherwise
        """
        collection = self._read_keyed_collection(ClaudeModel, self.COLLECTION_KEY)
        return collection.get(model_id)

    def get_by_pattern(self, model_string: str) -> Optional[ClaudeModel]:
        """
        Find a model that matches a model string by pattern.

        Args:
            model_string: Model identifier from transcript
                         (e.g., "claude-sonnet-4-5-20250929")

        Returns:
            Matching ClaudeModel, or None if no match
        """
        for model in self.list_all():
            if model.matches(model_string):
                return model
        return None

    def get_default(self) -> ClaudeModel:
        """
        Get the default model.

        Returns:
            Default ClaudeModel (falls back to Sonnet 4.5 if not configured)
        """
        data = self._read_json()
        default_id = data.get("default_model", "claude-sonnet-4.5")
        model = self.get(default_id)

        if model:
            return model

        # Ultimate fallback - hardcoded Sonnet 4.5
        return ClaudeModel(
            id="claude-sonnet-4.5",
            name="Claude Sonnet 4.5",
            description="Default model",
            pattern="*sonnet*",
            max_tokens=200000,
            pricing=ModelPricing(
                input=3.00,
                output=15.00,
                cache_write=3.75,
                cache_read=0.30,
            ),
        )

    def add(self, model: ClaudeModel) -> str:
        """
        Add a new model.

        Args:
            model: ClaudeModel to add

        Returns:
            The model ID

        Raises:
            ValueError: If model with same ID already exists
        """
        data = self._read_json()
        collection = self._read_keyed_collection(ClaudeModel, self.COLLECTION_KEY)

        if model.id in collection:
            raise ValueError(f"Model already exists: {model.id}")

        collection[model.id] = model

        # Preserve extra fields
        extra_fields = {
            "default_model": data.get("default_model", ""),
            "metadata": data.get("metadata", {}),
        }
        self._write_keyed_collection(collection, self.COLLECTION_KEY, extra_fields)

        return model.id

    def update(self, model: ClaudeModel) -> bool:
        """
        Update an existing model.

        Args:
            model: ClaudeModel with updated data

        Returns:
            True if updated, False if model not found
        """
        data = self._read_json()
        collection = self._read_keyed_collection(ClaudeModel, self.COLLECTION_KEY)

        if model.id not in collection:
            return False

        collection[model.id] = model

        # Preserve extra fields
        extra_fields = {
            "default_model": data.get("default_model", ""),
            "metadata": data.get("metadata", {}),
        }
        self._write_keyed_collection(collection, self.COLLECTION_KEY, extra_fields)

        return True

    def delete(self, model_id: str) -> bool:
        """
        Delete a model.

        Args:
            model_id: ID of model to delete

        Returns:
            True if deleted, False if not found
        """
        data = self._read_json()
        collection = self._read_keyed_collection(ClaudeModel, self.COLLECTION_KEY)

        if model_id not in collection:
            return False

        del collection[model_id]

        # If we deleted the default model, update to first remaining or empty
        default_model = data.get("default_model", "")
        if default_model == model_id:
            remaining = list(collection.keys())
            default_model = remaining[0] if remaining else ""

        # Preserve extra fields
        extra_fields = {
            "default_model": default_model,
            "metadata": data.get("metadata", {}),
        }
        self._write_keyed_collection(collection, self.COLLECTION_KEY, extra_fields)

        return True

    def set_default(self, model_id: str) -> bool:
        """
        Set the default model.

        Args:
            model_id: ID of model to set as default

        Returns:
            True if set, False if model not found
        """
        data = self._read_json()
        collection = self._read_keyed_collection(ClaudeModel, self.COLLECTION_KEY)

        if model_id not in collection:
            return False

        # Update default_model field
        extra_fields = {
            "default_model": model_id,
            "metadata": data.get("metadata", {}),
        }
        self._write_keyed_collection(collection, self.COLLECTION_KEY, extra_fields)

        return True

    # =========================================================================
    # Cost Extraction
    # =========================================================================

    def extract_from_transcript(self, transcript_path: str) -> dict:
        """
        Parse transcript JSONL file and extract usage data.

        Args:
            transcript_path: Path to the transcript JSONL file

        Returns:
            dict with keys:
                - input_tokens: int
                - output_tokens: int
                - cache_creation_tokens: int
                - cache_read_tokens: int
                - model: str (model identifier from transcript, or None)
        """
        result = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_tokens": 0,
            "cache_read_tokens": 0,
            "model": None,
        }

        transcript_file = Path(transcript_path)
        if not transcript_file.exists():
            return result

        try:
            with open(transcript_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Only process assistant messages
                    if entry.get("type") != "assistant":
                        continue

                    message = entry.get("message", {})
                    usage = message.get("usage")

                    if usage:
                        result["input_tokens"] += usage.get("input_tokens", 0)
                        result["output_tokens"] += usage.get("output_tokens", 0)
                        result["cache_creation_tokens"] += usage.get(
                            "cache_creation_input_tokens", 0
                        )
                        result["cache_read_tokens"] += usage.get("cache_read_input_tokens", 0)

                    # Capture model from first message that has it
                    if result["model"] is None:
                        model = message.get("model") or entry.get("model")
                        if model:
                            result["model"] = model

        except (OSError, IOError) as e:
            print(f"Error reading transcript: {e}")

        return result

    def calculate_cost(self, usage: dict) -> float:
        """
        Calculate USD cost from usage data.

        Args:
            usage: dict with token counts and optional model string

        Returns:
            Cost in USD as float
        """
        model_string = usage.get("model")
        model = None

        if model_string:
            model = self.get_by_pattern(model_string)

        if model is None:
            model = self.get_default()

        return model.calculate_cost(
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            cache_write_tokens=usage.get("cache_creation_tokens", 0),
            cache_read_tokens=usage.get("cache_read_tokens", 0),
        )

    def extract_and_store(
        self,
        task_id: str,
        transcript_path: str,
        session_id: str,
        queue_service,  # QueueService - avoid circular import
    ) -> Optional[float]:
        """
        Extract cost from transcript and store in task metadata.

        Args:
            task_id: The task ID to update
            transcript_path: Path to the transcript JSONL file
            session_id: Session identifier
            queue_service: QueueService instance for updating metadata

        Returns:
            Cost in USD, or None if no usage data found
        """
        # Extract usage data
        usage = self.extract_from_transcript(transcript_path)

        # Check if we have any usage data
        if usage["input_tokens"] == 0 and usage["output_tokens"] == 0:
            return None

        # Calculate cost
        cost_usd = self.calculate_cost(usage)

        # Get model name for display
        model_string = usage.get("model")
        model = None
        if model_string:
            model = self.get_by_pattern(model_string)
        if model is None:
            model = self.get_default()

        # Store in task metadata
        metadata_updates = {
            "cost_input_tokens": str(usage["input_tokens"]),
            "cost_output_tokens": str(usage["output_tokens"]),
            "cost_cache_creation_tokens": str(usage["cache_creation_tokens"]),
            "cost_cache_read_tokens": str(usage["cache_read_tokens"]),
            "cost_usd": f"{cost_usd:.4f}",
            "cost_model": model.name,
            "session_id": session_id,
        }

        for key, value in metadata_updates.items():
            queue_service.update_single_metadata(task_id, key, value)

        return cost_usd
