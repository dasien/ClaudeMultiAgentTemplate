"""
CMAT repositories.

Repositories handle low-level data persistence and retrieval,
abstracting storage mechanisms from the service layer.
"""

from .learnings_repository import LearningsRepository

__all__ = [
    "LearningsRepository",
]
