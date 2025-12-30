"""
ClaudeModel model for CMAT cost tracking.

Represents Claude model configurations including pricing information
for calculating workflow execution costs.
"""

from dataclasses import dataclass, field
import json
import re


@dataclass
class ModelPricing:
    """Pricing information for a Claude model."""
    input: float
    output: float
    cache_write: float
    cache_read: float
    currency: str = "USD"
    per_tokens: int = 1000000

    def calculate_cost(
            self,
            input_tokens: int = 0,
            output_tokens: int = 0,
            cache_write_tokens: int = 0,
            cache_read_tokens: int = 0,
    ) -> float:
        """Calculate total cost for given token counts."""
        factor = self.per_tokens
        return (
                (input_tokens * self.input / factor) +
                (output_tokens * self.output / factor) +
                (cache_write_tokens * self.cache_write / factor) +
                (cache_read_tokens * self.cache_read / factor)
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "input": self.input,
            "output": self.output,
            "cache_write": self.cache_write,
            "cache_read": self.cache_read,
            "currency": self.currency,
            "per_tokens": self.per_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ModelPricing":
        """Create ModelPricing from dictionary."""
        return cls(
            input=data["input"],
            output=data["output"],
            cache_write=data["cache_write"],
            cache_read=data["cache_read"],
            currency=data.get("currency", "USD"),
            per_tokens=data.get("per_tokens", 1000000),
        )


@dataclass
class ClaudeModel:
    """
    Represents a Claude model with its configuration and pricing.

    Models are defined in .claude/data/models.json and used for
    cost calculation and model selection.
    """
    id: str
    name: str
    description: str
    pattern: str
    max_tokens: int
    api_id: str = ""  # Actual Anthropic API model ID
    pricing: ModelPricing = field(default_factory=ModelPricing)

    def matches(self, model_string: str) -> bool:
        """Check if a model string matches this model's pattern."""
        patterns = self.pattern.split("|")
        for p in patterns:
            regex = p.replace("*", ".*")
            if re.match(regex, model_string):
                return True
        return False

    def calculate_cost(
            self,
            input_tokens: int = 0,
            output_tokens: int = 0,
            cache_write_tokens: int = 0,
            cache_read_tokens: int = 0,
    ) -> float:
        """Calculate total cost for given token counts."""
        return self.pricing.calculate_cost(
            input_tokens, output_tokens, cache_write_tokens, cache_read_tokens
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "pattern": self.pattern,
            "name": self.name,
            "description": self.description,
            "max_tokens": self.max_tokens,
            "api_id": self.api_id,
            "pricing": self.pricing.to_dict(),
        }

    @classmethod
    def from_dict(cls, model_id: str, data: dict) -> "ClaudeModel":
        """Create ClaudeModel from dictionary (e.g., loaded from JSON)."""
        return cls(
            id=model_id,
            name=data["name"],
            description=data["description"],
            pattern=data["pattern"],
            max_tokens=data["max_tokens"],
            api_id=data.get("api_id", model_id),  # Fall back to id if not specified
            pricing=ModelPricing.from_dict(data["pricing"]),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({self.id: self.to_dict()}, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ClaudeModel":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        model_id = list(data.keys())[0]
        return cls.from_dict(model_id, data[model_id])