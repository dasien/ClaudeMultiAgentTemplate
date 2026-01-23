"""
Utility functions for CMAT.

Provides shared utilities for timestamps, logging, path resolution,
directory management, dependency checking, and serialization.
"""

# Import all from common (previously utils.py)
from .common import (
    check_dependencies,
    configure_logging,
    ensure_directories,
    extract_enhancement_name,
    extract_enhancement_title,
    find_project_root,
    get_configured_project_root,
    get_datetime_utc,
    get_timestamp,
    log_error,
    log_info,
    log_operation,
    logger,
    needs_integration,
    set_project_root,
)

# Import serialization utilities
from .serialization import (
    datetime_to_iso,
    enum_to_value,
    iso_to_datetime,
    value_to_enum,
)

# Import stream formatting utilities
from .stream_formatter import (
    StreamFormatter,
    convert_log_file,
)

__all__ = [
    # Common utilities
    "logger",
    "set_project_root",
    "get_configured_project_root",
    "get_timestamp",
    "get_datetime_utc",
    "find_project_root",
    "ensure_directories",
    "log_operation",
    "log_error",
    "log_info",
    "check_dependencies",
    "extract_enhancement_name",
    "extract_enhancement_title",
    "needs_integration",
    "configure_logging",
    # Serialization utilities
    "datetime_to_iso",
    "iso_to_datetime",
    "enum_to_value",
    "value_to_enum",
    # Stream formatting utilities
    "StreamFormatter",
    "convert_log_file",
]
