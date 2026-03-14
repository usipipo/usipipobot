"""
Cache storage for uSipipo VPN Android APK.
Provides local encrypted caching with TTL support.
"""
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from loguru import logger

from kivy.utils import platform

from src.storage.secure_storage import SecureStorage


class CacheStorage:
    """
    Local cache storage with TTL support.

    Uses encrypted JSON file for persistence.
    Cache entries automatically expire based on TTL.
    """

    def __init__(self, ttl_seconds: int = 900):
        """
        Initialize cache storage.

        Args:
            ttl_seconds: Default TTL for cache entries (default: 15 minutes)
        """
        self.ttl_seconds = ttl_seconds
        self.cache_file = self._get_cache_path()
        self._ensure_cache_dir()
        self._cache: dict = {}
        self._load_cache()

    def _get_cache_path(self) -> str:
        """
        Get cache file path appropriate for the platform.

        On Android, uses the app's data directory.
        On desktop, uses ~/.usipipo_apk.

        Returns:
            Full path to cache.json file
        """
        if platform == 'android':
            try:
                from android.storage import app_storage_path
                cache_dir = app_storage_path()
            except ImportError:
                # Fallback if running on Android but android module not available
                cache_dir = os.path.join(os.path.expanduser("~"), ".usipipo_apk")
        else:
            # Desktop (Linux, macOS, Windows)
            cache_dir = os.path.join(os.path.expanduser("~"), ".usipipo_apk")
        
        return os.path.join(cache_dir, "cache.json")

    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        cache_dir = os.path.dirname(self.cache_file)
        os.makedirs(cache_dir, exist_ok=True)

    def _load_cache(self):
        """Load cache from disk."""
        try:
            if os.path.exists(self.cache_file):
                encrypted_data = SecureStorage.get_secret("cache_data")
                if encrypted_data:
                    cache_json = SecureStorage.decrypt(encrypted_data)
                    self._cache = json.loads(cache_json)
                    logger.debug(f"Cache loaded from {self.cache_file}")
        except Exception as e:
            logger.warning(f"Error loading cache: {e}")
            self._cache = {}

    def _save_cache(self):
        """Save cache to disk (encrypted)."""
        try:
            cache_json = json.dumps(self._cache)
            encrypted_data = SecureStorage.encrypt(cache_json)
            SecureStorage.set_secret("cache_data", encrypted_data)
            logger.debug(f"Cache saved to {self.cache_file}")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def _is_expired(self, entry: dict) -> bool:
        """Check if cache entry is expired."""
        try:
            expires_at_str = entry.get("expires_at")
            if not expires_at_str:
                return True
            
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) > expires_at
        except Exception as e:
            logger.warning(f"Error checking cache expiration: {e}")
            return True

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            entry = self._cache.get(key)
            if not entry:
                logger.debug(f"Cache miss for key: {key}")
                return None
            
            if self._is_expired(entry):
                logger.debug(f"Cache expired for key: {key}")
                self.delete(key)
                return None
            
            logger.debug(f"Cache hit for key: {key}")
            return entry.get("data")
            
        except Exception as e:
            logger.warning(f"Error getting cache key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional custom TTL (uses default if not provided)
        """
        try:
            ttl = ttl_seconds or self.ttl_seconds
            now = datetime.now(timezone.utc)
            
            entry = {
                "data": value,
                "cached_at": now.isoformat(),
                "expires_at": (now + timedelta(seconds=ttl)).isoformat()
            }
            
            self._cache[key] = entry
            self._save_cache()
            logger.debug(f"Cache set for key: {key} (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")

    def delete(self, key: str):
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        """
        try:
            if key in self._cache:
                del self._cache[key]
                self._save_cache()
                logger.debug(f"Cache deleted for key: {key}")
        except Exception as e:
            logger.warning(f"Error deleting cache key {key}: {e}")

    def clear(self):
        """Clear all cache entries."""
        try:
            self._cache = {}
            self._save_cache()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def cleanup_expired(self):
        """Remove all expired entries from cache."""
        try:
            expired_keys = [
                key for key, entry in self._cache.items()
                if self._is_expired(entry)
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                self._save_cache()
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
        except Exception as e:
            logger.warning(f"Error cleaning up cache: {e}")

    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats:
            - total_entries: Total number of entries
            - expired_entries: Number of expired entries
            - size_bytes: Approximate size in bytes
        """
        try:
            total = len(self._cache)
            expired = sum(1 for entry in self._cache.values() if self._is_expired(entry))
            size = len(json.dumps(self._cache))
            
            return {
                "total_entries": total,
                "expired_entries": expired,
                "size_bytes": size
            }
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {
                "total_entries": 0,
                "expired_entries": 0,
                "size_bytes": 0
            }
