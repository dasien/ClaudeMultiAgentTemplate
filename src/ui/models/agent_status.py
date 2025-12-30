"""
Agent status data model.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentStatus:
    """Agent status data model."""
    name: str
    status: str  # idle, active, blocked, error
    current_task: Optional[str] = None
    last_activity: Optional[str] = None