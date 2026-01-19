"""
CMAT - Claude Multi-Agent Template

A Python framework for orchestrating multi-agent workflows using Claude.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("cmat")
except PackageNotFoundError:
    # Package not installed (development mode without pip install -e)
    __version__ = "0.0.0-dev"

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
