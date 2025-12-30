"""
Agent model for CMAT workflow execution.

Agents are specialized AI personas configured with specific tools, skills,
and responsibilities for executing tasks within workflows.
"""

from dataclasses import dataclass, field
import json


@dataclass
class Agent:
    """
    Represents a specialized AI agent configured for specific tasks.

    Agents are defined in .claude/agents/agents.json and have corresponding
    markdown files containing their full persona and instructions.
    """
    name: str
    agent_file: str
    role: str
    description: str
    tools: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    validations: dict = field(default_factory=dict)

    def has_tool(self, tool_name: str) -> bool:
        """Check if agent has access to a specific tool."""
        return tool_name in self.tools

    def has_skill(self, skill_name: str) -> bool:
        """Check if agent has a specific skill."""
        return skill_name in self.skills

    def get_validation(self, key: str, default=None):
        """Get a validation setting by key."""
        return self.validations.get(key, default)

    def get_agent_file_path(self, agents_dir: str = ".claude/agents") -> str:
        """Get the full path to the agent's markdown file."""
        return f"{agents_dir}/{self.agent_file}.md"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "agent-file": self.agent_file,
            "role": self.role,
            "tools": self.tools,
            "skills": self.skills,
            "description": self.description,
            "validations": self.validations,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Agent":
        """Create Agent from dictionary (e.g., loaded from JSON)."""
        return cls(
            name=data["name"],
            agent_file=data["agent-file"],
            role=data["role"],
            description=data["description"],
            tools=data.get("tools", []),
            skills=data.get("skills", []),
            validations=data.get("validations", {}),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Agent":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))