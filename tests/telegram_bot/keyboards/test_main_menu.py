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
        """Test main menu with miniapp URL includes Mini App button."""
        miniapp_url = "https://app.example.com/miniapp/entry"
        result = MainMenuKeyboard.main_menu(miniapp_url=miniapp_url)
        
        assert isinstance(result, InlineKeyboardMarkup)
        assert len(result.inline_keyboard) == 3
        assert len(result.inline_keyboard[0]) == 3
        first_button = result.inline_keyboard[0][0]
        assert first_button.text == "📱 Mini App"
        assert first_button.web_app is not None
        assert first_button.web_app.url == miniapp_url

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
        assert len(result.inline_keyboard) == 4
        second_row = result.inline_keyboard[1]
        assert second_row[0].text == "📱 Mini App"
        assert second_row[0].web_app.url == miniapp_url

    def test_main_menu_with_admin_non_admin_user(self):
        """Test admin menu for non-admin user returns regular menu."""
        miniapp_url = "https://app.example.com/miniapp/entry"
        result = MainMenuKeyboard.main_menu_with_admin(
            admin_id=123, current_user_id=456, miniapp_url=miniapp_url
        )
        
        assert len(result.inline_keyboard) == 3
        assert result.inline_keyboard[0][0].text == "📱 Mini App"

    def test_main_menu_structure_consistency(self):
        """Test that menu structure is consistent across all variants."""
        miniapp_url = "https://app.example.com/miniapp/entry"
        
        menu_without_url = MainMenuKeyboard.main_menu()
        menu_with_url = MainMenuKeyboard.main_menu(miniapp_url=miniapp_url)
        
        assert len(menu_without_url.inline_keyboard) == len(menu_with_url.inline_keyboard)
        
        assert menu_without_url.inline_keyboard[1][0].text == "⚙️ Operaciones"
        assert menu_with_url.inline_keyboard[1][0].text == "⚙️ Operaciones"
        
        assert menu_without_url.inline_keyboard[2][0].text == "❓ Ayuda"
        assert menu_with_url.inline_keyboard[2][0].text == "❓ Ayuda"
