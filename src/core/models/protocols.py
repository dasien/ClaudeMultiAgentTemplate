"""Protocols defining model contracts."""

from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class Serializable(Protocol[T]):
    """
    Protocol for models that can be serialized to/from dict and JSON.

    All CMAT models should implement these four methods to ensure
    consistent serialization behavior across the system.

    Type parameter T represents the model class itself, enabling
    type-safe deserialization.

    Examples:
        >>> @dataclass
        ... class Task:
        ...     def to_dict(self) -> dict: ...
        ...     @classmethod
        ...     def from_dict(cls, data: dict) -> "Task": ...
        ...     def to_json(self) -> str: ...
        ...     @classmethod
        ...     def from_json(cls, json_str: str) -> "Task": ...

        >>> isinstance(Task, Serializable)  # True at runtime

    Notes:
        - @runtime_checkable allows isinstance/issubclass checks
        - Generic type T enables mypy to verify return types
        - Protocol is structural (duck typing) not nominal
        - Models don't need to explicitly inherit this protocol
    """

    def to_dict(self) -> dict:
        """
        Convert model to dictionary representation.

        Returns:
            Dictionary suitable for JSON serialization
        """
        ...

    @classmethod
    def from_dict(cls, data: dict) -> T:
        """
        Create model instance from dictionary.

        Args:
            data: Dictionary representation of the model

        Returns:
            New instance of the model class
        """
        ...

    def to_json(self) -> str:
        """
        Convert model to JSON string.

        Returns:
            JSON string representation
        """
        ...

    @classmethod
    def from_json(cls, json_str: str) -> T:
        """
        Create model instance from JSON string.

        Args:
            json_str: JSON string representation

        Returns:
            New instance of the model class
        """
        ...
