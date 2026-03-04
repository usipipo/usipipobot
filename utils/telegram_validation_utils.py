"""
Telegram Text Validation & Sanitization Utilities

This module provides text validation, sanitization, and escaping
functions for Telegram messages.

Author: uSipipo Team
"""

import re


def sanitize_text(text: str, max_length: int | None = None) -> str:
    """
    Sanitize text for Telegram messages.

    Args:
        text: Text to sanitize
        max_length: Maximum length (optional)

    Returns:
        str: Sanitized text
    """
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text.strip())

    if max_length and len(text) > max_length:
        text = text[: max_length - 3] + "..."

    return text


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format.

    Args:
        phone: Phone number string

    Returns:
        bool: True if valid
    """
    # Remove all non-digit characters
    digits = re.sub(r"\D", "", phone)

    # Check if it has reasonable length (10-15 digits)
    return 10 <= len(digits) <= 15


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email string

    Returns:
        bool: True if valid
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def escape_markdown(text: str) -> str:
    """
    Escape markdown special characters for Telegram Markdown (legacy).

    For standard Markdown mode, only backticks and backslashes within
    inline code contexts need escaping. This function maintains compatibility
    with existing code while supporting the standardized Markdown mode.

    Args:
        text: Text to escape

    Returns:
        str: Text safe for Markdown (minimal escaping)
    """
    if not text:
        return text

    # Only escape backticks to prevent breaking inline code formatting
    text = text.replace("`", "\\`")

    return text


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        str: Truncated string
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix
