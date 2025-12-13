"""
Enhancement model for CMAT workflow targets.

Represents an enhancement (feature, bugfix, etc.) that workflows operate on.
Enhancements are filesystem-based, living in the enhancements/ directory.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import json


@dataclass
class Enhancement:
    """
    Represents an enhancement that workflows operate on.

    Enhancements are created in the enhancements/{name}/ directory
    with a {name}.md file containing the enhancement specification.
    This model provides a programmatic interface to enhancement data.
    """
    name: str
    path: Path
    created: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)

    @property
    def spec_file(self) -> Path:
        """Path to the enhancement specification markdown file."""
        return self.path / f"{self.name}.md"

    @property
    def exists(self) -> bool:
        """Check if the enhancement directory and spec file exist."""
        return self.path.exists() and self.spec_file.exists()

    def get_agent_output_dir(self, agent_name: str) -> Path:
        """Get the output directory for a specific agent."""
        return self.path / agent_name

    def get_agent_required_output_dir(self, agent_name: str) -> Path:
        """Get the required output directory for a specific agent."""
        return self.get_agent_output_dir(agent_name) / "required_output"

    def get_agent_optional_output_dir(self, agent_name: str) -> Path:
        """Get the optional output directory for a specific agent."""
        return self.get_agent_output_dir(agent_name) / "optional_output"

    def list_agent_outputs(self) -> list[str]:
        """List agents that have produced output for this enhancement."""
        if not self.path.exists():
            return []
        return [
            d.name for d in self.path.iterdir()
            if d.is_dir() and d.name != self.name and not d.name.startswith(".")
        ]

    def read_spec(self) -> Optional[str]:
        """Read the enhancement specification content."""
        if self.spec_file.exists():
            return self.spec_file.read_text()
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "path": str(self.path),
            "created": self.created.isoformat() if self.created else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Enhancement":
        """Create Enhancement from dictionary."""
        return cls(
            name=data["name"],
            path=Path(data["path"]),
            created=datetime.fromisoformat(data["created"]) if data.get("created") else None,
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_path(cls, path: Path) -> "Enhancement":
        """Create Enhancement from a directory path."""
        name = path.name
        created = None
        if path.exists():
            created = datetime.fromtimestamp(path.stat().st_ctime, tz=timezone.utc)
        return cls(name=name, path=path, created=created)

    @classmethod
    def from_name(cls, name: str, enhancements_dir: str = "enhancements") -> "Enhancement":
        """Create Enhancement from a name, using default enhancements directory."""
        path = Path(enhancements_dir) / name
        return cls.from_path(path)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Enhancement":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))