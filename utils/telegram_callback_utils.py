"""
Telegram Callback Data & General Helpers

This module provides callback data manipulation, pagination,
and general-purpose helper functions for Telegram handlers.

Author: uSipipo Team
"""

import re
from typing import Any, Dict, List, Optional


def extract_id_from_callback(callback_data: str, prefix: str) -> Optional[int]:
    """
    Extract ID from callback data.

    Args:
        callback_data: Callback data string
        prefix: Prefix to look for

    Returns:
        int or None: Extracted ID
    """
    pattern = f"^{prefix}_(\\d+)$"
    match = re.match(pattern, callback_data)

    if match:
        return int(match.group(1))

    return None


def create_callback_data(prefix: str, *args) -> str:
    """
    Create callback data from parts.

    Args:
        prefix: Prefix for the callback
        *args: Additional parts

    Returns:
        str: Callback data string
    """
    parts = [prefix] + [str(arg) for arg in args]
    return "_".join(parts)


def parse_callback_data(callback_data: str) -> List[str]:
    """
    Parse callback data into parts.

    Args:
        callback_data: Callback data string

    Returns:
        list: Parts of the callback data
    """
    return callback_data.split("_")


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary.

    Args:
        dictionary: Dictionary to get value from
        key: Key to look for
        default: Default value if key not found

    Returns:
        Any: Value or default
    """
    return dictionary.get(key, default)


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks.

    Args:
        items: List to chunk
        chunk_size: Size of each chunk

    Returns:
        list: List of chunks
    """
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def generate_unique_id() -> str:
    """
    Generate a unique ID.

    Returns:
        str: Unique ID
    """
    import uuid

    return str(uuid.uuid4())[:8]


def is_admin(user_id: int) -> bool:
    """
    Check if user is admin.

    Args:
        user_id: User ID to check

    Returns:
        bool: True if admin
    """
    from config import settings

    return user_id == int(settings.ADMIN_ID)


def calculate_page_bounds(
    total_items: int, page: int, items_per_page: int = 10
) -> tuple:
    """
    Calculate page bounds for pagination.

    Args:
        total_items: Total number of items
        page: Current page (0-based)
        items_per_page: Items per page

    Returns:
        tuple: (start_idx, end_idx, total_pages)
    """
    total_pages = (total_items + items_per_page - 1) // items_per_page
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)

    return start_idx, end_idx, total_pages
