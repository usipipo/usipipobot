"""
Tests for cache storage.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from src.storage.cache_storage import CacheStorage


class TestCacheStorage:
    """Test cache storage functionality."""

    @pytest.fixture
    def mock_secure_storage(self):
        """Mock secure storage."""
        with patch("src.storage.cache_storage.SecureStorage") as mock:
            mock.get_secret = MagicMock(return_value=None)
            mock.set_secret = MagicMock()
            yield mock

    @pytest.fixture
    def cache_storage(self, mock_secure_storage, tmp_path):
        """Create cache storage instance with temp directory."""
        with patch("src.storage.cache_storage.SecureStorage", mock_secure_storage):
            with patch.object(CacheStorage, "_ensure_cache_dir"):
                storage = CacheStorage(ttl_seconds=900)
                storage.cache_file = str(tmp_path / "cache.json")
                return storage

    def test_init(self, cache_storage):
        """Test cache storage initialization."""
        assert cache_storage.ttl_seconds == 900
        assert isinstance(cache_storage._cache, dict)

    def test_set_and_get(self, cache_storage):
        """Test setting and getting cache values."""
        # Arrange
        cache_storage.set("test_key", {"data": "test_value"})

        # Act
        result = cache_storage.get("test_key")

        # Assert
        assert result == {"data": "test_value"}

    def test_get_nonexistent_key(self, cache_storage):
        """Test getting nonexistent key returns None."""
        result = cache_storage.get("nonexistent")
        assert result is None

    def test_expired_entry(self, cache_storage):
        """Test expired cache entry returns None."""
        # Arrange
        expired_entry = {
            "data": "test",
            "cached_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
        }
        cache_storage._cache["expired_key"] = expired_entry

        # Act
        result = cache_storage.get("expired_key")

        # Assert
        assert result is None
        assert "expired_key" not in cache_storage._cache  # Should be deleted

    def test_delete(self, cache_storage):
        """Test deleting cache entry."""
        # Arrange
        cache_storage.set("to_delete", "value")
        assert cache_storage.get("to_delete") is not None

        # Act
        cache_storage.delete("to_delete")

        # Assert
        assert cache_storage.get("to_delete") is None

    def test_clear(self, cache_storage):
        """Test clearing all cache entries."""
        # Arrange
        cache_storage.set("key1", "value1")
        cache_storage.set("key2", "value2")
        assert len(cache_storage._cache) == 2

        # Act
        cache_storage.clear()

        # Assert
        assert len(cache_storage._cache) == 0

    def test_cleanup_expired(self, cache_storage):
        """Test cleaning up expired entries."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Valid entry
        cache_storage._cache["valid"] = {
            "data": "valid",
            "cached_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
        }

        # Expired entry
        cache_storage._cache["expired"] = {
            "data": "expired",
            "cached_at": (now - timedelta(hours=2)).isoformat(),
            "expires_at": (now - timedelta(hours=1)).isoformat(),
        }

        # Act
        cache_storage.cleanup_expired()

        # Assert
        assert "valid" in cache_storage._cache
        assert "expired" not in cache_storage._cache

    def test_get_stats(self, cache_storage):
        """Test cache statistics."""
        # Arrange
        now = datetime.now(timezone.utc)

        cache_storage._cache["valid"] = {
            "data": "valid",
            "cached_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
        }

        cache_storage._cache["expired"] = {
            "data": "expired",
            "cached_at": (now - timedelta(hours=2)).isoformat(),
            "expires_at": (now - timedelta(hours=1)).isoformat(),
        }

        # Act
        stats = cache_storage.get_stats()

        # Assert
        assert stats["total_entries"] == 2
        assert stats["expired_entries"] == 1
        assert stats["size_bytes"] > 0

    def test_custom_ttl(self, cache_storage):
        """Test setting entry with custom TTL."""
        # Arrange
        custom_ttl = 60  # 1 minute

        # Act
        cache_storage.set("custom_ttl_key", "value", ttl_seconds=custom_ttl)

        # Assert
        entry = cache_storage._cache["custom_ttl_key"]
        expires_at = datetime.fromisoformat(entry["expires_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        expected_expiry = now + timedelta(seconds=custom_ttl)

        # Allow 1 second variance
        assert abs((expires_at - expected_expiry).total_seconds()) < 1

    def test_is_expired_edge_cases(self, cache_storage):
        """Test expiration check edge cases."""
        # Entry without expires_at
        entry_no_expiry = {"data": "test"}
        assert cache_storage._is_expired(entry_no_expiry) is True

        # Entry with invalid expires_at
        entry_invalid = {"data": "test", "expires_at": "invalid"}
        assert cache_storage._is_expired(entry_invalid) is True

    def test_load_cache_error_handling(self, mock_secure_storage):
        """Test error handling when loading cache fails."""
        # Arrange
        mock_secure_storage.get_secret.side_effect = Exception("Test error")

        # Act
        storage = CacheStorage()

        # Assert
        assert storage._cache == {}  # Should default to empty dict

    def test_save_cache_error_handling(self, cache_storage, mock_secure_storage):
        """Test error handling when saving cache fails."""
        # Arrange
        mock_secure_storage.set_secret.side_effect = Exception("Test error")

        # Act & Assert
        cache_storage.set("test", "value")  # Should not raise
        # Cache in memory should still work
        assert cache_storage.get("test") is not None


class TestCacheStorageIntegration:
    """Integration tests for cache storage."""

    def test_full_cache_lifecycle(self, tmp_path):
        """Test complete cache lifecycle."""
        # This would test with real file system
        # Skipped in CI
        pytest.skip("Integration test - requires real file system")
