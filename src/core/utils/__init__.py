"""
CMAT utility functions.

This package provides utilities for:
- Project root discovery and directory management
- Logging and timestamps
- Dependency checking
- Serialization helpers
"""

from .common import (
    find_project_root,
    ensure_directories,
    check_dependencies,
    configure_logging,
    set_project_root,
    get_configured_project_root,
    get_timestamp,
    get_datetime_utc,
    log_operation,
    log_error,
    log_info,
    extract_enhancement_name,
    extract_enhancement_title,
    needs_integration,
)

from .serialization import (
    datetime_to_iso,
    iso_to_datetime,
    enum_to_value,
    value_to_enum,
)

__all__ = [
    # Common utilities
    "find_project_root",
    "ensure_directories",
    "check_dependencies",
    "configure_logging",
    "set_project_root",
    "get_configured_project_root",
    "get_timestamp",
    "get_datetime_utc",
    "log_operation",
    "log_error",
    "log_info",
    "extract_enhancement_name",
    "extract_enhancement_title",
    "needs_integration",
    # Serialization utilities
    "datetime_to_iso",
    "iso_to_datetime",
    "enum_to_value",
    "value_to_enum",
]
