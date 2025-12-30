"""
Agent persona data model.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class AgentPersona:
    """Agent persona data model (predefined agent type with tool preset)."""
    key: str
    display_name: str
    description: str
    tools: List[str]  # List of tool names

    @staticmethod
    def from_dict(key: str, data: dict) -> 'AgentPersona':
        """Create AgentPersona from dictionary (e.g., from tools.json).

        Args:
            key: The persona key (e.g., 'analyst', 'architect')
            data: Dictionary containing persona data

        Returns:
            AgentPersona instance
        """
        return AgentPersona(
            key=key,
            display_name=data.get('display_name', key),
            description=data.get('description', ''),
            tools=data.get('tools', [])
        )

    def to_dict(self) -> dict:
        """Convert AgentPersona to dictionary for JSON serialization.

        Returns:
            Dictionary representation (without key)
        """
        return {
            'display_name': self.display_name,
            'description': self.description,
            'tools': self.tools
        }