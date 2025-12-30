"""
Skill model for CMAT agent capabilities.

Skills are reusable knowledge modules that can be assigned to agents,
providing domain-specific expertise and approaches.
"""

from dataclasses import dataclass, field
import json


@dataclass
class Skill:
    """
    Represents a reusable skill that can be assigned to agents.

    Skills are defined in .claude/skills/skills.json and have corresponding
    directories containing their SKILL.md documentation.
    """
    name: str
    skill_directory: str
    category: str
    description: str
    required_tools: list[str] = field(default_factory=list)

    def requires_tool(self, tool_name: str) -> bool:
        """Check if skill requires a specific tool."""
        return tool_name in self.required_tools

    def get_skill_file_path(self, skills_dir: str = ".claude/skills") -> str:
        """Get the full path to the skill's markdown file."""
        return f"{skills_dir}/{self.skill_directory}/SKILL.md"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "skill-directory": self.skill_directory,
            "category": self.category,
            "required_tools": self.required_tools,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Skill":
        """Create Skill from dictionary (e.g., loaded from JSON)."""
        return cls(
            name=data["name"],
            skill_directory=data["skill-directory"],
            category=data["category"],
            description=data["description"],
            required_tools=data.get("required_tools", []),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Skill":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
