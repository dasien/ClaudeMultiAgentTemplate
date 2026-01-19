"""Serialization utilities for consistent data conversion."""

from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

T = TypeVar("T", bound=Enum)


def datetime_to_iso(dt: datetime | None) -> str | None:
    """
    Convert datetime to ISO 8601 string with Z suffix.

    Args:
        dt: datetime object to convert, or None

    Returns:
        ISO 8601 string with trailing "Z", or None if input is None

    Examples:
        >>> from datetime import datetime, timezone
        >>> datetime_to_iso(datetime(2025, 1, 17, 12, 0, 0, tzinfo=timezone.utc))
        '2025-01-17T12:00:00+00:00Z'

        >>> datetime_to_iso(None)
        None

    Notes:
        - Always appends "Z" if not already present
        - Preserves existing timezone information in isoformat
        - Consistent with existing model behavior
    """
    if dt is None:
        return None
    iso_str = dt.isoformat()
    return iso_str if iso_str.endswith("Z") else iso_str + "Z"


def iso_to_datetime(iso_str: str | None) -> datetime | None:
    """
    Convert ISO 8601 string to datetime, handling Z suffix.

    Args:
        iso_str: ISO 8601 formatted string, or None

    Returns:
        datetime object, or None if input is None

    Examples:
        >>> iso_to_datetime('2025-01-17T12:00:00Z')
        datetime.datetime(2025, 1, 17, 12, 0, 0)

        >>> iso_to_datetime(None)
        None

    Notes:
        - Strips trailing "Z" before parsing (fromisoformat doesn't handle it)
        - Preserves timezone info if present
        - Matches existing model deserialization behavior
    """
    if iso_str is None:
        return None
    return datetime.fromisoformat(iso_str.rstrip("Z"))


def enum_to_value(obj: Enum) -> Any:
    """
    Extract value from enum instance.

    Args:
        obj: Enum instance

    Returns:
        The enum's value

    Examples:
        >>> from enum import Enum
        >>> class Status(Enum):
        ...     PENDING = "pending"
        >>> enum_to_value(Status.PENDING)
        'pending'

    Notes:
        - Generic function works with any Enum subclass
        - Simply extracts .value attribute
        - Used in to_dict() methods
    """
    return obj.value


def value_to_enum(enum_class: type[T], value: Any) -> T:
    """
    Convert value to enum instance.

    Args:
        enum_class: The enum class to instantiate
        value: The value to convert

    Returns:
        Enum instance of the specified class

    Examples:
        >>> from enum import Enum
        >>> class Status(Enum):
        ...     PENDING = "pending"
        >>> value_to_enum(Status, "pending")
        <Status.PENDING: 'pending'>

    Notes:
        - Type-safe with generic TypeVar
        - Raises ValueError if value not in enum
        - Used in from_dict() methods
    """
    return enum_class(value)
