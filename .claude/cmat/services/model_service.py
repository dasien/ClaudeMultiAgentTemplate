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

from cmat.models.claude_model import ClaudeModel, ModelPricing
from cmat.utils import find_project_root


class ModelService:
    """
    Service for managing Claude models and calculating costs.

    Provides CRUD operations for model definitions and cost extraction
    from Claude transcripts.
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize ModelService.

        Args:
            data_dir: Path to data directory containing models.json.
                     If None, uses default location via find_project_root().
        """
        if data_dir is None:
            project_root = find_project_root()
            if project_root:
                self._data_dir = project_root / ".claude/data"
            else:
                self._data_dir = Path(".claude/data")
        else:
            self._data_dir = Path(data_dir)

        self._models_file = self._data_dir / "models.json"
        self._cache: Optional[dict] = None

    def _ensure_file_exists(self) -> None:
        """Ensure models.json exists with default content."""
        if not self._models_file.exists():
            self._data_dir.mkdir(parents=True, exist_ok=True)
            default_data = {
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
                    "last_updated": "",
                    "pricing_source": "https://www.anthropic.com/pricing",
                },
            }
            with open(self._models_file, "w") as f:
                json.dump(default_data, f, indent=2)
            self._cache = default_data

    def _load(self) -> dict:
        """Load models.json and cache it."""
        if self._cache is not None:
            return self._cache

        self._ensure_file_exists()

        with open(self._models_file) as f:
            self._cache = json.load(f)
        return self._cache

    def _save(self, data: dict) -> None:
        """Save data to models.json and update cache."""
        self._data_dir.mkdir(parents=True, exist_ok=True)
        with open(self._models_file, "w") as f:
            json.dump(data, f, indent=2)
        self._cache = data

    def invalidate_cache(self) -> None:
        """Clear the cache to force reload from disk."""
        self._cache = None

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def list_all(self) -> list[ClaudeModel]:
        """
        List all available models.

        Returns:
            List of ClaudeModel objects
        """
        data = self._load()
        models = []
        for model_id, model_data in data.get("models", {}).items():
            models.append(ClaudeModel.from_dict(model_id, model_data))
        return models

    def get(self, model_id: str) -> Optional[ClaudeModel]:
        """
        Get a model by its ID.

        Args:
            model_id: The model ID (e.g., "claude-sonnet-4.5")

        Returns:
            ClaudeModel if found, None otherwise
        """
        data = self._load()
        model_data = data.get("models", {}).get(model_id)
        if model_data:
            return ClaudeModel.from_dict(model_id, model_data)
        return None

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
        data = self._load()
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
        data = self._load()

        if model.id in data.get("models", {}):
            raise ValueError(f"Model already exists: {model.id}")

        if "models" not in data:
            data["models"] = {}

        data["models"][model.id] = model.to_dict()
        self._save(data)

        return model.id

    def update(self, model: ClaudeModel) -> bool:
        """
        Update an existing model.

        Args:
            model: ClaudeModel with updated data

        Returns:
            True if updated, False if model not found
        """
        data = self._load()

        if model.id not in data.get("models", {}):
            return False

        data["models"][model.id] = model.to_dict()
        self._save(data)

        return True

    def delete(self, model_id: str) -> bool:
        """
        Delete a model.

        Args:
            model_id: ID of model to delete

        Returns:
            True if deleted, False if not found
        """
        data = self._load()

        if model_id not in data.get("models", {}):
            return False

        del data["models"][model_id]

        # If we deleted the default model, clear the default
        if data.get("default_model") == model_id:
            remaining = list(data.get("models", {}).keys())
            data["default_model"] = remaining[0] if remaining else ""

        self._save(data)

        return True

    def set_default(self, model_id: str) -> bool:
        """
        Set the default model.

        Args:
            model_id: ID of model to set as default

        Returns:
            True if set, False if model not found
        """
        data = self._load()

        if model_id not in data.get("models", {}):
            return False

        data["default_model"] = model_id
        self._save(data)

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
                        result["cache_read_tokens"] += usage.get(
                            "cache_read_input_tokens", 0
                        )

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