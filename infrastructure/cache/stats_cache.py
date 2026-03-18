"""
Redis cache for server statistics.

Provides caching layer for ServerStats with TTL and rolling history.
"""

import json
from dataclasses import asdict
from typing import Any, Optional

import redis.asyncio as redis

from utils.logger import logger

STATS_LATEST_KEY = "server:stats:latest"
STATS_HISTORY_KEY = "server:stats:history"
STATS_TTL = 300  # 5 minutes


class ServerStats:
    """Server performance and status metrics."""

    def __init__(
        self,
        timestamp: str,
        ping_ms: float,
        cpu_percent: float,
        ram_percent: float,
        ram_used_mb: int,
        ram_total_mb: int,
        active_wg_connections: int,
        outline_status: bool,
        wireguard_status: bool,
        dnsproxy_status: bool,
        uptime_hours: float,
    ):
        self.timestamp = timestamp
        self.ping_ms = ping_ms
        self.cpu_percent = cpu_percent
        self.ram_percent = ram_percent
        self.ram_used_mb = ram_used_mb
        self.ram_total_mb = ram_total_mb
        self.active_wg_connections = active_wg_connections
        self.outline_status = outline_status
        self.wireguard_status = wireguard_status
        self.dnsproxy_status = dnsproxy_status
        self.uptime_hours = uptime_hours

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "ping_ms": self.ping_ms,
            "cpu_percent": self.cpu_percent,
            "ram_percent": self.ram_percent,
            "ram_used_mb": self.ram_used_mb,
            "ram_total_mb": self.ram_total_mb,
            "active_wg_connections": self.active_wg_connections,
            "outline_status": self.outline_status,
            "wireguard_status": self.wireguard_status,
            "dnsproxy_status": self.dnsproxy_status,
            "uptime_hours": self.uptime_hours,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @property
    def quality_score(self) -> int:
        """Calculate quality score 0-100 based on key metrics."""
        score = 100
        if self.ping_ms > 200:
            score -= 40
        elif self.ping_ms > 100:
            score -= 20
        elif self.ping_ms > 50:
            score -= 10
        if self.cpu_percent > 85:
            score -= 30
        elif self.cpu_percent > 60:
            score -= 15
        if self.ram_percent > 90:
            score -= 30
        elif self.ram_percent > 75:
            score -= 15
        return max(0, score)

    @property
    def status_label(self) -> tuple[str, str]:
        """Get status emoji and label based on quality score."""
        score = self.quality_score
        if score >= 75:
            return "🟢", "Excelente"
        elif score >= 50:
            return "🟡", "Normal"
        else:
            return "🔴", "Alta carga"


STATS_LATEST_KEY = "server:stats:latest"
STATS_HISTORY_KEY = "server:stats:history"
STATS_TTL = 300  # 5 minutes


async def save_stats(stats: ServerStats, redis_client: redis.Redis) -> None:
    """
    Save server stats to Redis with TTL.

    - Stores latest stats in STATS_LATEST_KEY
    - Pushes to history list (keeps last 10 entries)

    Args:
        stats: ServerStats instance to save
        redis_client: Redis async client
    """
    try:
        stats_json = stats.to_json()

        # Save latest with TTL
        await redis_client.setex(STATS_LATEST_KEY, STATS_TTL, stats_json)

        # Push to history and trim to last 10
        await redis_client.lpush(STATS_HISTORY_KEY, stats_json)
        await redis_client.ltrim(STATS_HISTORY_KEY, 0, 9)

        logger.debug(f"📊 Server stats saved to cache (ping: {stats.ping_ms}ms)")
    except Exception as e:
        logger.error(f"❌ Failed to save server stats to Redis: {e}")


async def get_latest_stats(redis_client: redis.Redis) -> Optional[ServerStats]:
    """
    Get latest server stats from Redis cache.

    Args:
        redis_client: Redis async client

    Returns:
        ServerStats instance or None if not available
    """
    try:
        raw = await redis_client.get(STATS_LATEST_KEY)
        if not raw:
            return None

        data = json.loads(raw)
        return ServerStats(**data)
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse server stats from Redis: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to get server stats from Redis: {e}")
        return None


async def get_stats_history(redis_client: redis.Redis) -> list[ServerStats]:
    """
    Get rolling history of server stats (last 10 measurements).

    Args:
        redis_client: Redis async client

    Returns:
        List of ServerStats instances (newest first)
    """
    try:
        items = await redis_client.lrange(STATS_HISTORY_KEY, 0, 9)
        if not items:
            return []

        return [ServerStats(**json.loads(item)) for item in items]
    except Exception as e:
        logger.error(f"❌ Failed to get server stats history from Redis: {e}")
        return []


async def clear_stats_cache(redis_client: redis.Redis) -> None:
    """
    Clear all server stats from cache.

    Useful for testing or manual reset.

    Args:
        redis_client: Redis async client
    """
    try:
        await redis_client.delete(STATS_LATEST_KEY, STATS_HISTORY_KEY)
        logger.info("🗑️ Server stats cache cleared")
    except Exception as e:
        logger.error(f"❌ Failed to clear server stats cache: {e}")
