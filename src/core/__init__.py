"""
CMAT - Claude Multi-Agent Template

A Python framework for orchestrating multi-agent workflows using Claude.
"""

__version__ = "10.2.0"

from .cmat import CMAT
from .utils import (
    find_project_root,
    ensure_directories,
    check_dependencies,
    configure_logging,
    set_project_root,
)

__all__ = [
    "CMAT",
    "find_project_root",
    "ensure_directories",
    "check_dependencies",
    "configure_logging",
    "set_project_root",
    "__version__",
]
