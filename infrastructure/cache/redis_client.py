"""
Redis client utilities.

Provides helper functions to get Redis client instances.
"""

import redis.asyncio as redis

from config import settings


def get_redis_client() -> redis.Redis:
    """
    Get Redis async client from settings.

    Returns:
        Redis async client instance
    """
    return redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
