"""
Tests for MainMenuKeyboard with Mini App button.

Author: uSipipo Team
Version: 1.0.0
"""

import pytest
from telegram import InlineKeyboardMarkup, WebAppInfo

from telegram_bot.keyboards.main_menu import MainMenuKeyboard


class TestMainMenuKeyboard:
    """Test main menu keyboard functionality."""

    def test_main_menu_without_miniapp_url(self):
        """Test main menu without miniapp URL (backward compatibility)."""
        result = MainMenuKeyboard.main_menu()

        assert isinstance(result, InlineKeyboardMarkup)
        assert len(result.inline_keyboard) == 3
        assert len(result.inline_keyboard[0]) == 2
        assert result.inline_keyboard[0][0].text == "🔑 Mis Claves VPN"

    def test_main_menu_with_miniapp_url(self):
        """Test main menu with miniapp URL includes Mini App button in separate row."""
        miniapp_url = "https://app.example.com/miniapp/entry"
        result = MainMenuKeyboard.main_menu(miniapp_url=miniapp_url)

        assert isinstance(result, InlineKeyboardMarkup)
        assert len(result.inline_keyboard) == 4
        first_row = result.inline_keyboard[0]
        assert len(first_row) == 1
        assert first_row[0].text == "📱 Mini App"
        assert first_row[0].web_app is not None
        assert first_row[0].web_app.url == miniapp_url

        second_row = result.inline_keyboard[1]
        assert len(second_row) == 2
        assert second_row[0].text == "🔑 Mis Claves VPN"
        assert second_row[1].text == "➕ Nueva Clave"

    def test_main_menu_with_none_miniapp_url(self):
        """Test main menu with explicitly None miniapp URL."""
        result = MainMenuKeyboard.main_menu(miniapp_url=None)

        assert isinstance(result, InlineKeyboardMarkup)
        assert len(result.inline_keyboard) == 3
        assert len(result.inline_keyboard[0]) == 2
        assert result.inline_keyboard[0][0].text == "🔑 Mis Claves VPN"

    def test_main_menu_with_admin_without_miniapp(self):
        """Test admin menu without miniapp URL."""
        result = MainMenuKeyboard.main_menu_with_admin(
            admin_id=123, current_user_id=123
        )

        assert isinstance(result, InlineKeyboardMarkup)
        assert len(result.inline_keyboard) == 4
        assert result.inline_keyboard[0][0].text == "🔧 Admin"

    def test_main_menu_with_admin_with_miniapp(self):
        """Test admin menu with miniapp URL."""
        miniapp_url = "https://app.example.com/miniapp/entry"
        result = MainMenuKeyboard.main_menu_with_admin(
            admin_id=123, current_user_id=123, miniapp_url=miniapp_url
        )

        assert isinstance(result, InlineKeyboardMarkup)
        assert len(result.inline_keyboard) == 5
        assert result.inline_keyboard[0][0].text == "🔧 Admin"
        miniapp_row = result.inline_keyboard[1]
        assert len(miniapp_row) == 1
        assert miniapp_row[0].text == "📱 Mini App"
        assert miniapp_row[0].web_app is not None
        assert miniapp_row[0].web_app.url == miniapp_url

        keys_row = result.inline_keyboard[2]
        assert len(keys_row) == 2
        assert keys_row[0].text == "🔑 Mis Claves VPN"
        assert keys_row[1].text == "➕ Nueva Clave"

    def test_main_menu_with_admin_non_admin_user(self):
        """Test admin menu for non-admin user returns regular menu."""
        miniapp_url = "https://app.example.com/miniapp/entry"
        result = MainMenuKeyboard.main_menu_with_admin(
            admin_id=123, current_user_id=456, miniapp_url=miniapp_url
        )

        assert len(result.inline_keyboard) == 4
        assert result.inline_keyboard[0][0].text == "📱 Mini App"
        assert len(result.inline_keyboard[0]) == 1

    def test_main_menu_structure_consistency(self):
        """Test that menu structure is consistent across all variants."""
        miniapp_url = "https://app.example.com/miniapp/entry"

        menu_without_url = MainMenuKeyboard.main_menu()
        menu_with_url = MainMenuKeyboard.main_menu(miniapp_url=miniapp_url)

        assert len(menu_without_url.inline_keyboard) == 3
        assert len(menu_with_url.inline_keyboard) == 4

        assert menu_without_url.inline_keyboard[0][0].text == "🔑 Mis Claves VPN"
        assert menu_with_url.inline_keyboard[0][0].text == "📱 Mini App"
        assert menu_with_url.inline_keyboard[1][0].text == "🔑 Mis Claves VPN"

        assert menu_without_url.inline_keyboard[1][0].text == "⚙️ Operaciones"
        assert menu_with_url.inline_keyboard[2][0].text == "⚙️ Operaciones"

        assert menu_without_url.inline_keyboard[2][0].text == "❓ Ayuda"
        assert menu_with_url.inline_keyboard[3][0].text == "❓ Ayuda"
