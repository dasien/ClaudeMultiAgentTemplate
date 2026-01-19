"""
CMAT UI - Multi-Agent Task Queue Manager

A graphical interface for managing multi-agent development workflows
using the Claude Multi-Agent Development Template.
"""

from core import __version__

from .main import main, MainView
from .config import Config

__all__ = ["main", "MainView", "Config"]