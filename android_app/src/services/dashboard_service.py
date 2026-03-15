"""
Dashboard service for uSipipo VPN Android APK.
Handles dashboard data fetching and caching.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from loguru import logger
from src.services.api_client import ApiClient
from src.storage.cache_storage import CacheStorage


class DashboardService:
    """Service for dashboard operations with caching support."""

    # Cache TTL: 15 minutes
    CACHE_TTL_SECONDS = 900

    def __init__(self, telegram_id: str):
        self.telegram_id = telegram_id
        self.api_client = ApiClient(telegram_id=telegram_id)
        self.cache_storage = CacheStorage()

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Get dashboard summary data.

        Uses local cache if available and not expired (15-min TTL).
        Falls back to API call if cache is missing or expired.

        Returns:
            Dict with dashboard data:
            - user: user info (name, username, photo_url, status, etc.)
            - data_summary: total used/limit bytes
            - active_keys: list of active VPN keys
            - active_package: current package info (if any)
            - referral_credits: number of referral credits
            - has_pending_debt: bool
            - consumption_mode_enabled: bool
            - last_login: datetime

        Raises:
            httpx.HTTPStatusError: If API call fails
            httpx.RequestError: If network error occurs
        """
        cache_key = f"dashboard:{self.telegram_id}"

        # Try to get from cache first
        try:
            cached_data = self.cache_storage.get(cache_key)
            if cached_data:
                logger.debug(f"Dashboard cache hit for user {self.telegram_id}")
                return cached_data
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")

        # Cache miss or error: fetch from API
        logger.debug(f"Dashboard cache miss for user {self.telegram_id}, fetching from API")

        try:
            response = await self.api_client.get(endpoint="/dashboard/summary", use_auth=True)

            # Store in cache with timestamp
            cache_entry = {
                "data": response,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (
                    datetime.now(timezone.utc) + timedelta(seconds=self.CACHE_TTL_SECONDS)
                ).isoformat(),
            }

            try:
                self.cache_storage.set(cache_key, cache_entry)
                logger.debug(f"Dashboard data cached for user {self.telegram_id}")
            except Exception as e:
                logger.warning(f"Error writing cache: {e}")

            return response

        except Exception as e:
            logger.error(f"Error fetching dashboard data: {e}")

            # If we have stale cache, return it as fallback
            try:
                stale_cache = self.cache_storage.get(cache_key)
                if stale_cache:
                    logger.warning(f"Returning stale cache for user {self.telegram_id}")
                    return stale_cache.get("data", stale_cache)
            except:
                pass

            raise

    async def refresh_dashboard(self) -> Dict[str, Any]:
        """
        Force refresh dashboard data from API (bypass cache).

        Returns:
            Dict with fresh dashboard data
        """
        cache_key = f"dashboard:{self.telegram_id}"

        logger.info(f"Refreshing dashboard data for user {self.telegram_id}")

        response = await self.api_client.get(endpoint="/dashboard/summary", use_auth=True)

        # Update cache
        cache_entry = {
            "data": response,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(seconds=self.CACHE_TTL_SECONDS)
            ).isoformat(),
        }

        try:
            self.cache_storage.set(cache_key, cache_entry)
        except Exception as e:
            logger.warning(f"Error updating cache after refresh: {e}")

        return response

    def clear_cache(self):
        """Clear dashboard cache for current user."""
        cache_key = f"dashboard:{self.telegram_id}"
        try:
            self.cache_storage.delete(cache_key)
            logger.debug(f"Dashboard cache cleared for user {self.telegram_id}")
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")

    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """Format bytes to human-readable string (GB, MB)."""
        if bytes_value >= 1_073_741_824:  # 1 GB
            return f"{bytes_value / 1_073_741_824:.2f} GB"
        elif bytes_value >= 1_048_576:  # 1 MB
            return f"{bytes_value / 1_048_576:.2f} MB"
        elif bytes_value >= 1_024:  # 1 KB
            return f"{bytes_value / 1_024:.2f} KB"
        else:
            return f"{bytes_value} B"

    @staticmethod
    def calculate_percentage(used: int, total: int) -> float:
        """Calculate usage percentage (0-100)."""
        if total == 0:
            return 0.0
        return min(100.0, (used / total) * 100)

    @staticmethod
    def get_progress_color(percentage: float) -> str:
        """Get progress bar color based on percentage."""
        if percentage <= 60:
            return "neon_cyan"  # #00f0ff
        elif percentage <= 85:
            return "amber"  # #ff9500
        else:
            return "error"  # #ff4444

    @staticmethod
    def format_relative_time(dt_str: Optional[str]) -> str:
        """Format datetime to relative time string (e.g., 'hace 2 horas')."""
        if not dt_str:
            return "Nunca"

        try:
            # Parse ISO format datetime
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            diff = now - dt

            seconds = diff.total_seconds()
            minutes = seconds / 60
            hours = minutes / 60
            days = hours / 24

            if seconds < 60:
                return "ahora mismo"
            elif minutes < 60:
                return f"hace {int(minutes)}m"
            elif hours < 24:
                return f"hace {int(hours)}h"
            elif days < 30:
                return f"hace {int(days)}d"
            else:
                return dt.strftime("%d/%m/%Y")

        except Exception as e:
            logger.warning(f"Error formatting time {dt_str}: {e}")
            return "Desconocido"
