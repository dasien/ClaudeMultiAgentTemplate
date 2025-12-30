"""
Queue UI state data model.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from .connection_state import ConnectionState
from .task import Task


@dataclass
class QueueUIState:
    """UI state data model."""
    connection_state: ConnectionState = ConnectionState.DISCONNECTED
    queue_manager_path: Optional[Path] = None
    project_root: Optional[Path] = None
    queue_file: Optional[Path] = None
    logs_dir: Optional[Path] = None
    selected_task: Optional[Task] = None
    auto_refresh_enabled: bool = True
    auto_refresh_interval: int = 3  # seconds
    last_refresh: float = 0.0
    error_message: str = ""