"""
Telegram Formatting Utilities

This module provides formatting functions for displaying data
in Telegram messages (bytes, dates, currencies, percentages, user names).

Author: uSipipo Team
"""

from datetime import datetime


def format_bytes(bytes_count: int) -> str:
    """
    Format bytes into human readable format.

    Args:
        bytes_count: Number of bytes

    Returns:
        str: Formatted string (e.g., "1.5 GB")
    """
    if bytes_count == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    value = float(bytes_count)

    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024.0
        unit_index += 1

    return f"{value:.1f} {units[unit_index]}"


def format_datetime(dt: datetime, include_time: bool = True) -> str:
    """
    Format datetime in user-friendly format.

    Args:
        dt: DateTime object
        include_time: Whether to include time

    Returns:
        str: Formatted datetime string
    """
    if include_time:
        return dt.strftime("%d/%m/%Y %H:%M")
    return dt.strftime("%d/%m/%Y")


def format_relative_time(dt: datetime) -> str:
    """
    Format datetime as relative time (e.g., "hace 2 horas").

    Args:
        dt: DateTime object

    Returns:
        str: Relative time string
    """
    now = datetime.now()
    delta = now - dt

    if delta.days > 0:
        if delta.days == 1:
            return "ayer"
        elif delta.days < 7:
            return f"hace {delta.days} días"
        elif delta.days < 30:
            weeks = delta.days // 7
            return f"hace {weeks} semana{'s' if weeks > 1 else ''}"
        else:
            months = delta.days // 30
            return f"hace {months} mes{'es' if months > 1 else ''}"

    hours = delta.seconds // 3600
    if hours > 0:
        return f"hace {hours} hora{'s' if hours > 1 else ''}"

    minutes = (delta.seconds % 3600) // 60
    if minutes > 0:
        return f"hace {minutes} minuto{'s' if minutes > 1 else ''}"

    return "ahora mismo"


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format currency amount.

    Args:
        amount: Amount to format
        currency: Currency code

    Returns:
        str: Formatted currency string
    """
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}

    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:.2f}"


def format_percentage(value: float, total: float) -> str:
    """
    Format percentage with progress bar.

    Args:
        value: Current value
        total: Total value

    Returns:
        str: Formatted percentage with progress bar
    """
    if total == 0:
        percentage = 0.0
    else:
        percentage = min(100.0, (value / total) * 100)

    # Create progress bar
    bar_length = 10
    filled_length = int(bar_length * percentage / 100)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    return f"{bar} {percentage:.1f}%"


def format_user_name(user) -> str:
    """
    Format user name for display.

    Args:
        user: Telegram user object

    Returns:
        str: Formatted name
    """
    if user.full_name:
        return user.full_name
    elif user.username:
        return f"@{user.username}"
    else:
        return f"Usuario {user.id}"
