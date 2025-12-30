"""
Agent data model.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Agent:
    """Agent data model."""
    name: str
    agent_file: str
    tools: List[str]
    description: str

    @staticmethod
    def from_dict(data: dict) -> 'Agent':
        """Create Agent from dictionary (e.g., from agents.json).

        Args:
            data: Dictionary containing agent data

        Returns:
            Agent instance
        """
        return Agent(
            name=data.get('name', ''),
            agent_file=data.get('agent-file', ''),
            tools=data.get('tools', []),
            description=data.get('description', '')
        )

    def to_dict(self) -> dict:
        """Convert Agent to dictionary for JSON serialization.

        Returns:
            Dictionary representation
        """
        return {
            'name': self.name,
            'agent-file': self.agent_file,
            'tools': self.tools,
            'description': self.description
        }