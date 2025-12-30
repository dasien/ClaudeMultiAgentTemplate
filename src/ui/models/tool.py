"""
Tool data model.
"""

from dataclasses import dataclass


@dataclass
class Tool:
    """Tool data model."""
    name: str
    display_name: str
    description: str

    @staticmethod
    def from_dict(data: dict) -> 'Tool':
        """Create Tool from dictionary (e.g., from tools.json).

        Args:
            data: Dictionary containing tool data

        Returns:
            Tool instance
        """
        return Tool(
            name=data.get('name', ''),
            display_name=data.get('display_name', data.get('name', '')),
            description=data.get('description', '')
        )

    def to_dict(self) -> dict:
        """Convert Tool to dictionary for JSON serialization.

        Returns:
            Dictionary representation
        """
        return {
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description
        }