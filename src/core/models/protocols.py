"""Protocols defining model contracts."""

from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar('T')


@runtime_checkable
class Serializable(Protocol[T]):
    """
    Protocol for models that can be serialized to/from dict and JSON.

    All models should implement these methods for consistent serialization.
    Using @runtime_checkable allows isinstance() checks.
    """

    def to_dict(self) -> dict:
        """Convert model to dictionary representation."""
        ...

    @classmethod
    def from_dict(cls, data: dict) -> T:
        """Create model instance from dictionary."""
        ...

    def to_json(self) -> str:
        """Convert model to JSON string."""
        ...

    @classmethod
    def from_json(cls, json_str: str) -> T:
        """Create model instance from JSON string."""
        ...
