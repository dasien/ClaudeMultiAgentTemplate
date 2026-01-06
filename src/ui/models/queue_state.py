"""
Queue state data model.
"""

from dataclasses import dataclass
from typing import List

from core.models import Task


@dataclass
class QueueState:
    """Queue state data model."""
    pending_tasks: List[Task]
    active_workflows: List[Task]
    completed_tasks: List[Task]
    failed_tasks: List[Task]
    cancelled_tasks: List[Task]