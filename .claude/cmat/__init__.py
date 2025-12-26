"""
CMAT - Claude Multi-Agent Template

A Python framework for orchestrating multi-agent workflows using Claude.
"""

# Enable running from source without installation
# This adds the .claude directory to sys.path if cmat isn't installed
import sys
from pathlib import Path

_package_dir = Path(__file__).parent.parent
if str(_package_dir) not in sys.path:
    sys.path.insert(0, str(_package_dir))

__version__ = "8.8.0"
from .cmat import CMAT
from .utils import (
    find_project_root,
    ensure_directories,
    check_dependencies,
    configure_logging,
)

__all__ = [
    "CMAT",
    "find_project_root",
    "ensure_directories",
    "check_dependencies",
    "configure_logging",
    "__version__"
]
