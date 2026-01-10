"""
Text utility functions.
"""

import re


def to_slug(text: str) -> str:
    """
    Convert text to slug format (lowercase-with-hyphens).
    
    Args:
        text: Input text (e.g., "My Feature Name")
    
    Returns:
        Slug format string (e.g., "my-feature-name")
    
    Examples:
        >>> to_slug("AI Assistant Feature")
        'ai-assistant-feature'
        
        >>> to_slug("Bug Fix: Login Page")
        'bug-fix-login-page'
        
        >>> to_slug("  Multiple   Spaces  ")
        'multiple-spaces'
    """
    # Convert to lowercase
    slug = text.lower()
    
    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Strip leading/trailing hyphens
    slug = slug.strip('-')
    
    return slug


def validate_slug(slug: str) -> bool:
    """
    Check if a string is a valid slug format.

    Args:
        slug: String to validate

    Returns:
        True if valid slug (lowercase, numbers, hyphens only)

    Examples:
        >>> validate_slug("my-feature")
        True

        >>> validate_slug("My-Feature")
        False

        >>> validate_slug("my_feature")
        False
    """
    return bool(re.match(r'^[a-z0-9-]+$', slug))


def slug_to_display(slug: str) -> str:
    """
    Convert a slug (kebab-case or snake_case) to a UI-friendly display name.

    This is the inverse of to_slug().

    Args:
        slug: Slug format string (e.g., "my-feature-name" or "code_reviewer")

    Returns:
        Title case display string (e.g., "My Feature Name" or "Code Reviewer")

    Examples:
        >>> slug_to_display("new-feature-enhancement")
        'New Feature Enhancement'

        >>> slug_to_display("code_reviewer")
        'Code Reviewer'

        >>> slug_to_display("architect")
        'Architect'

        >>> slug_to_display("")
        ''
    """
    if not slug:
        return ''
    # Replace hyphens and underscores with spaces, then title case
    return slug.replace('-', ' ').replace('_', ' ').title()
