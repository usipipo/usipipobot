"""
Preferences storage for non-sensitive app preferences.
Uses JSON file for simple key-value storage.
"""
import json
import os
from loguru import logger

from src.config import APP_DATA_DIR


class PreferencesStorage:
    """Storage for app preferences (non-sensitive data)."""

    FILE_PATH = os.path.join(APP_DATA_DIR, "preferences.json")

    @staticmethod
    def _ensure_dir():
        """Ensure data directory exists."""
        os.makedirs(APP_DATA_DIR, exist_ok=True)

    @staticmethod
    def _read() -> dict:
        """Read preferences from file."""
        PreferencesStorage._ensure_dir()
        if not os.path.exists(PreferencesStorage.FILE_PATH):
            return {}
        try:
            with open(PreferencesStorage.FILE_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    @staticmethod
    def _write(data: dict) -> None:
        """Write preferences to file."""
        PreferencesStorage._ensure_dir()
        with open(PreferencesStorage.FILE_PATH, "w") as f:
            json.dump(data, f)

    @staticmethod
    def get_last_user_id() -> str | None:
        """Get last logged-in user telegram_id."""
        data = PreferencesStorage._read()
        return data.get("last_telegram_id")

    @staticmethod
    def set_last_user_id(telegram_id: str) -> None:
        """Set last logged-in user telegram_id."""
        data = PreferencesStorage._read()
        data["last_telegram_id"] = telegram_id
        PreferencesStorage._write(data)
        logger.debug(f"Last user ID saved: {telegram_id}")

    @staticmethod
    def clear() -> None:
        """Clear all preferences."""
        if os.path.exists(PreferencesStorage.FILE_PATH):
            os.remove(PreferencesStorage.FILE_PATH)
