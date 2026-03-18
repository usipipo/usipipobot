"""
Server latency API endpoint for Mini App.

Provides real-time server metrics (latency, CPU, RAM, connections)
for the Telegram Mini App dashboard.
"""

from fastapi import APIRouter, Depends

from infrastructure.cache.redis_client import get_redis_client
from infrastructure.cache.stats_cache import get_latest_stats, get_stats_history, save_stats
from infrastructure.metrics import collect_server_stats
from utils.logger import logger

router = APIRouter(prefix="/api", tags=["Server Metrics"])


@router.get("/latency")
async def get_server_latency(redis_client=Depends(get_redis_client)):
    """
    Get current server latency and performance metrics.

    Returns cached stats if available (< 5 min), otherwise collects fresh metrics.

    Response format:
    ```json
    {
        "status": "ok",
        "current": {
            "timestamp": "2026-03-18T12:34:56Z",
            "ping_ms": 23.5,
            "cpu_percent": 42.1,
            "ram_percent": 61.3,
            "ram_used_mb": 1248,
            "ram_total_mb": 2048,
            "active_wg_connections": 12,
            "outline_status": true,
            "wireguard_status": true,
            "dnsproxy_status": false,
            "uptime_hours": 168.5
        },
        "quality_score": 85,
        "status_icon": "🟢",
        "status_label": "Excelente",
        "history": [...]
    }
    ```
    """
    try:
        # Try to get cached stats
        stats = await get_latest_stats(redis_client)

        if not stats:
            # No stats available - collect fresh
            logger.info("📊 No cached stats, collecting fresh metrics")
            stats = await collect_server_stats()
            await save_stats(stats, redis_client)

        # Get history for charts
        history = await get_stats_history(redis_client)

        icon, label = stats.status_label

        return {
            "status": "ok",
            "current": stats.to_dict(),
            "quality_score": stats.quality_score,
            "status_icon": icon,
            "status_label": label,
            "history": [s.to_dict() for s in history],
        }

    except Exception as e:
        logger.error(f"❌ Error getting server latency: {e}")
        return {
            "status": "error",
            "message": "Failed to retrieve server metrics",
        }


@router.post("/latency/refresh")
async def refresh_server_latency(redis_client=Depends(get_redis_client)):
    """
    Force refresh of server latency metrics.

    Collects fresh metrics regardless of cache.
    Useful for manual refresh in the Mini App.
    """
    try:
        logger.info("🔄 Forced refresh of server metrics")

        # Collect fresh stats
        stats = await collect_server_stats()
        await save_stats(stats, redis_client)

        icon, label = stats.status_label

        return {
            "status": "ok",
            "current": stats.to_dict(),
            "quality_score": stats.quality_score,
            "status_icon": icon,
            "status_label": label,
        }

    except Exception as e:
        logger.error(f"❌ Error refreshing server latency: {e}")
        return {
            "status": "error",
            "message": "Failed to refresh server metrics",
        }
