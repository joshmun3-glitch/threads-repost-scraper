"""Validation utilities for Threads Scraper."""

import re
from typing import Optional


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_username(username: str) -> str:
    """
    Validate a Threads username.

    Args:
        username: The username to validate

    Returns:
        Cleaned username (without @ prefix if present)

    Raises:
        ValidationError: If username is invalid
    """
    if not username:
        raise ValidationError("Username cannot be empty")

    # Remove @ prefix if present
    cleaned = username.lstrip('@')

    # Validate format (alphanumeric, underscores, dots, 1-30 characters)
    pattern = r'^[a-zA-Z0-9._]{1,30}$'
    if not re.match(pattern, cleaned):
        raise ValidationError(
            f"Invalid username format: {username}. "
            "Username must be 1-30 characters and contain only letters, numbers, dots, and underscores."
        )

    # Additional checks
    if cleaned.startswith('.') or cleaned.endswith('.'):
        raise ValidationError("Username cannot start or end with a dot")

    if '..' in cleaned:
        raise ValidationError("Username cannot contain consecutive dots")

    return cleaned


def validate_url(url: str, expected_domain: Optional[str] = None) -> bool:
    """
    Validate a URL format.

    Args:
        url: The URL to validate
        expected_domain: Optional domain that must be present in URL

    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False

    # Basic URL pattern
    url_pattern = r'^https?://'
    if not re.match(url_pattern, url):
        return False

    # Check domain if specified
    if expected_domain:
        return expected_domain in url

    return True


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    Sanitize a filename by removing/replacing invalid characters.

    Args:
        filename: The filename to sanitize
        max_length: Maximum length for the filename

    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters for Windows/Unix
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, '_', filename)

    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    # Ensure it's not empty
    if not sanitized:
        sanitized = 'untitled'

    return sanitized
