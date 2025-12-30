"""
Task data model.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Task:
    """Task data model."""
    id: str
    title: str
    assigned_agent: str
    priority: str
    task_type: str
    description: str
    source_file: str
    created: str
    status: str
    started: Optional[str] = None
    completed: Optional[str] = None
    result: Optional[str] = None
    start_datetime: Optional[int] = None  # Unix timestamp
    end_datetime: Optional[int] = None    # Unix timestamp
    runtime_seconds: Optional[int] = None
    auto_complete: bool = False
    auto_chain: bool = False
    metadata: Optional[dict] = None