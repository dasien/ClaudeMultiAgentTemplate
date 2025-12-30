"""
Time utility functions.
"""

from typing import Optional


class TimeUtils:
    """Utilities for time formatting and display."""
    
    @staticmethod
    def format_runtime(seconds: Optional[int]) -> str:
        """
        Format runtime in human-readable form.
        
        Args:
            seconds: Runtime in seconds (can be None)
        
        Returns:
            Formatted string like "45s", "2m 30s", "1h 15m"
            Returns empty string if seconds is None/0
        
        Examples:
            >>> TimeUtils.format_runtime(45)
            '45s'
            
            >>> TimeUtils.format_runtime(150)
            '2m 30s'
            
            >>> TimeUtils.format_runtime(3665)
            '1h 1m'
            
            >>> TimeUtils.format_runtime(None)
            ''
        """
        if not seconds:
            return ""
        
        seconds = int(seconds)
        
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            mins = seconds // 60
            secs = seconds % 60
            return f"{mins}m {secs}s"
        else:
            hours = seconds // 3600
            mins = (seconds % 3600) // 60
            return f"{hours}h {mins}m"
