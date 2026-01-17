"""Serialization utilities for consistent data conversion."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, TypeVar

T = TypeVar('T', bound=Enum)


def datetime_to_iso(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert datetime to ISO format string with Z suffix.

    Args:
        dt: Datetime object or None

    Returns:
        ISO format string with Z suffix, or None if input is None

    Example:
        >>> datetime_to_iso(datetime(2024, 1, 15, 12, 0, 0))
        '2024-01-15T12:00:00Z'
    """
    if dt is None:
        return None
    # Ensure consistent Z suffix for UTC
    iso_str = dt.isoformat()
    return iso_str if iso_str.endswith("Z") else iso_str + "Z"


def iso_to_datetime(iso_str: Optional[str]) -> Optional[datetime]:
    """
    Convert ISO format string to datetime, handling Z suffix.

    Args:
        iso_str: ISO format string (with or without Z suffix) or None

    Returns:
        datetime object or None if input is None

    Example:
        >>> iso_to_datetime('2024-01-15T12:00:00Z')
        datetime(2024, 1, 15, 12, 0, 0)
    """
    if iso_str is None:
        return None
    # Strip Z suffix for fromisoformat compatibility
    return datetime.fromisoformat(iso_str.rstrip("Z"))


def enum_to_value(obj: Enum) -> Any:
    """
    Convert enum to its value.

    Args:
        obj: Enum instance

    Returns:
        The enum's value

    Example:
        >>> enum_to_value(TaskStatus.ACTIVE)
        'active'
    """
    return obj.value


def value_to_enum(enum_class: type[T], value: Any) -> T:
    """
    Convert value to enum instance.

    Args:
        enum_class: The enum class to instantiate
        value: The value to convert

    Returns:
        Enum instance

    Example:
        >>> value_to_enum(TaskStatus, 'active')
        TaskStatus.ACTIVE
    """
    return enum_class(value)
