"""
Connection state enumeration.
"""

from enum import Enum


class ConnectionState(Enum):
    """Connection state enum."""
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    ERROR = "error"