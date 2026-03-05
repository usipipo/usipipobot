"""
Tests for KeyManagementKeyboards.

Author: uSipipo Team
Version: 1.0.0
"""

import pytest
from telegram import InlineKeyboardMarkup

from telegram_bot.features.key_management.keyboards_key_management import (
    KeyManagementKeyboards,
)


class TestKeyManagementKeyboards:
    """Test key management keyboard functionality."""

    def test_main_menu_without_consumption_active(self):
        """Test main menu shows 'Activar Consumo' when no active consumption."""
        keys_summary = {"total_count": 2, "outline_count": 1, "wireguard_count": 1}

        result = KeyManagementKeyboards.main_menu(
            keys_summary, has_consumption_active=False
        )

        assert isinstance(result, InlineKeyboardMarkup)
        # First button should be "Activar Consumo"
        first_row = result.inline_keyboard[0]
        assert len(first_row) == 1
        assert first_row[0].text == "⚡ Activar Consumo"
        assert first_row[0].callback_data == "consumption_activate"

    def test_main_menu_with_consumption_active(self):
        """Test main menu shows 'Ver Mi Consumo' when consumption is active."""
        keys_summary = {"total_count": 2, "outline_count": 1, "wireguard_count": 1}

        result = KeyManagementKeyboards.main_menu(
            keys_summary, has_consumption_active=True
        )

        assert isinstance(result, InlineKeyboardMarkup)
        # First button should be "Ver Mi Consumo"
        first_row = result.inline_keyboard[0]
        assert len(first_row) == 1
        assert first_row[0].text == "📊 Ver Mi Consumo"
        assert first_row[0].callback_data == "consumption_view_status"

    def test_main_menu_default_no_consumption(self):
        """Test main menu defaults to no consumption active when not specified."""
        keys_summary = {"total_count": 2, "outline_count": 1, "wireguard_count": 1}

        # Call without has_consumption_active parameter
        result = KeyManagementKeyboards.main_menu(keys_summary)

        assert isinstance(result, InlineKeyboardMarkup)
        # Should default to "Activar Consumo"
        first_row = result.inline_keyboard[0]
        assert first_row[0].text == "⚡ Activar Consumo"

    def test_main_menu_with_empty_keys(self):
        """Test main menu with no keys still shows consumption button."""
        keys_summary = {"total_count": 0}

        result = KeyManagementKeyboards.main_menu(
            keys_summary, has_consumption_active=False
        )

        assert isinstance(result, InlineKeyboardMarkup)
        # Should still have consumption button
        assert result.inline_keyboard[0][0].text == "⚡ Activar Consumo"

    def test_main_menu_structure_with_keys(self):
        """Test main menu structure when user has keys."""
        keys_summary = {"total_count": 2, "outline_count": 1, "wireguard_count": 1}

        result = KeyManagementKeyboards.main_menu(
            keys_summary, has_consumption_active=True
        )

        # Should have: consumption button, keys row, actions row, back button
        assert len(result.inline_keyboard) >= 3
        # Consumption button
        assert result.inline_keyboard[0][0].text == "📊 Ver Mi Consumo"
        # Keys row (outline + wireguard)
        keys_row = result.inline_keyboard[1]
        assert len(keys_row) == 2
        assert "Outline" in keys_row[0].text
        assert "WireGuard" in keys_row[1].text

    def test_main_menu_only_outline_keys(self):
        """Test main menu with only Outline keys."""
        keys_summary = {"total_count": 1, "outline_count": 1, "wireguard_count": 0}

        result = KeyManagementKeyboards.main_menu(
            keys_summary, has_consumption_active=True
        )

        # Keys row should only have Outline
        keys_row = result.inline_keyboard[1]
        assert len(keys_row) == 1
        assert "Outline" in keys_row[0].text

    def test_main_menu_only_wireguard_keys(self):
        """Test main menu with only WireGuard keys."""
        keys_summary = {"total_count": 1, "outline_count": 0, "wireguard_count": 1}

        result = KeyManagementKeyboards.main_menu(
            keys_summary, has_consumption_active=True
        )

        # Keys row should only have WireGuard
        keys_row = result.inline_keyboard[1]
        assert len(keys_row) == 1
        assert "WireGuard" in keys_row[0].text
