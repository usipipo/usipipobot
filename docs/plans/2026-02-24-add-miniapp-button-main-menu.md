# Add Mini App Button to Main Menu Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a WebApp button to the Telegram bot's main menu that opens the Mini App directly from the first row.

**Architecture:** Modify MainMenuKeyboard class to include a WebAppInfo button that opens the Mini App URL. The button will be conditionally shown based on MINIAPP_ENABLED setting and requires MINIAPP_URL configuration.

**Tech Stack:** Python, python-telegram-bot (WebAppInfo), Pydantic Settings

---

## Overview

Currently the Mini App exists and is fully functional at `/miniapp/entry`, but there's no way for users to access it directly from the Telegram bot menu. This plan adds a prominent button to the main menu that opens the Mini App.

## Current State

**MainMenuKeyboard.main_menu() returns:**
```
Row 1: [🔑 Mis Claves VPN] [➕ Nueva Clave]
Row 2: [⚙️ Operaciones] [💾 Mis Datos]
Row 3: [❓ Ayuda]
```

## Target State

**MainMenuKeyboard.main_menu(miniapp_url) returns:**
```
Row 1: [📱 Mini App] [🔑 Mis Claves VPN] [➕ Nueva Clave]
Row 2: [⚙️ Operaciones] [💾 Mis Datos]
Row 3: [❓ Ayuda]
```

---

## Task 1: Update MainMenuKeyboard with WebApp Button

**Files:**
- Modify: `telegram_bot/keyboards/main_menu.py`

**Step 1: Add WebAppInfo import and modify main_menu method**

```python
"""
Menú principal del bot uSipipo.

Author: uSipipo Team
Version: 1.1.0 - Added Mini App button
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


class MainMenuKeyboard:
    """Teclado del menú principal simplificado."""

    @staticmethod
    def main_menu(miniapp_url: str | None = None) -> InlineKeyboardMarkup:
        keyboard = []
        
        # First row with Mini App button (if URL provided)
        if miniapp_url:
            keyboard.append([
                InlineKeyboardButton("📱 Mini App", web_app=WebAppInfo(url=miniapp_url)),
                InlineKeyboardButton("🔑 Mis Claves VPN", callback_data="show_keys"),
                InlineKeyboardButton("➕ Nueva Clave", callback_data="create_key"),
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("🔑 Mis Claves VPN", callback_data="show_keys"),
                InlineKeyboardButton("➕ Nueva Clave", callback_data="create_key"),
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("⚙️ Operaciones", callback_data="operations_menu"),
                InlineKeyboardButton("💾 Mis Datos", callback_data="show_usage"),
            ],
            [InlineKeyboardButton("❓ Ayuda", callback_data="help")],
        ])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def main_menu_with_admin(
        admin_id: int, current_user_id: int, miniapp_url: str | None = None
    ) -> InlineKeyboardMarkup:
        if str(current_user_id) == str(admin_id):
            keyboard = [
                [InlineKeyboardButton("🔧 Admin", callback_data="admin_panel")],
            ]
            
            # Second row with Mini App button (if URL provided)
            if miniapp_url:
                keyboard.append([
                    InlineKeyboardButton("📱 Mini App", web_app=WebAppInfo(url=miniapp_url)),
                    InlineKeyboardButton("🔑 Mis Claves VPN", callback_data="show_keys"),
                    InlineKeyboardButton("➕ Nueva Clave", callback_data="create_key"),
                ])
            else:
                keyboard.append([
                    InlineKeyboardButton("🔑 Mis Claves VPN", callback_data="show_keys"),
                    InlineKeyboardButton("➕ Nueva Clave", callback_data="create_key"),
                ])
            
            keyboard.extend([
                [
                    InlineKeyboardButton("⚙️ Operaciones", callback_data="operations_menu"),
                    InlineKeyboardButton("💾 Mis Datos", callback_data="show_usage"),
                ],
                [InlineKeyboardButton("❓ Ayuda", callback_data="help")],
            ])
            return InlineKeyboardMarkup(keyboard)
        return MainMenuKeyboard.main_menu(miniapp_url)
```

**Step 2: Commit changes**

```bash
git add telegram_bot/keyboards/main_menu.py
git commit -m "feat: add Mini App button to main menu keyboard"
```

---

## Task 2: Update CommonKeyboards.main_menu Wrapper

**Files:**
- Modify: `telegram_bot/common/keyboards.py`

**Step 1: Update main_menu method to pass miniapp_url**

```python
@staticmethod
def main_menu(is_admin: bool = False, miniapp_url: str | None = None) -> InlineKeyboardMarkup:
    """
    Main menu keyboard.

    NOTE: Para el menú principal simplificado, usar:
    from telegram_bot.keyboards import MainMenuKeyboard
    MainMenuKeyboard.main_menu(miniapp_url)
    """
    from telegram_bot.keyboards import MainMenuKeyboard

    if is_admin:
        from config import settings

        return MainMenuKeyboard.main_menu_with_admin(
            admin_id=int(settings.ADMIN_ID), 
            current_user_id=int(settings.ADMIN_ID),
            miniapp_url=miniapp_url
        )
    return MainMenuKeyboard.main_menu(miniapp_url)
```

**Step 2: Commit changes**

```bash
git add telegram_bot/common/keyboards.py
git commit -m "feat: pass miniapp_url to MainMenuKeyboard"
```

---

## Task 3: Update Handler to Pass MiniApp URL

**Files:**
- Find handlers that show main menu and update them

**Step 1: Search for main menu usage**

Run: `grep -r "main_menu()" telegram_bot/handlers/ telegram_bot/features/`
Expected: List of files that call main_menu()

**Step 2: Identify key handler file**

The main menu is typically shown after `/start` command and when returning from submenus.

**Step 3: Update handlers to pass MINIAPP_URL**

Key files to check:
- `telegram_bot/features/user_management/handlers_user_management.py` (main_menu callback)
- `telegram_bot/handlers/` (start command handler)

Pattern to use:
```python
from config import settings

# In handler:
miniapp_url = None
if settings.MINIAPP_ENABLED and settings.MINIAPP_URL:
    miniapp_url = f"{settings.MINIAPP_URL.rstrip('/')}/miniapp/entry"

keyboard = MainMenuKeyboard.main_menu(miniapp_url)
```

**Step 4: Commit changes**

```bash
git add telegram_bot/features/user_management/handlers_user_management.py
git commit -m "feat: pass MINIAPP_URL to main menu keyboard"
```

---

## Task 4: Update Tests

**Files:**
- Modify: `tests/telegram_bot/keyboards/test_main_menu.py` (if exists)
- Create if not exists

**Step 1: Write tests for new functionality**

```python
"""Tests for MainMenuKeyboard with Mini App button."""

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
        # First row should have 2 buttons (no Mini App)
        assert len(result.inline_keyboard[0]) == 2
        assert result.inline_keyboard[0][0].text == "🔑 Mis Claves VPN"

    def test_main_menu_with_miniapp_url(self):
        """Test main menu with miniapp URL includes Mini App button."""
        miniapp_url = "https://app.example.com/miniapp/entry"
        result = MainMenuKeyboard.main_menu(miniapp_url=miniapp_url)
        
        assert isinstance(result, InlineKeyboardMarkup)
        assert len(result.inline_keyboard) == 3
        # First row should have 3 buttons (including Mini App)
        assert len(result.inline_keyboard[0]) == 3
        # First button should be Mini App
        first_button = result.inline_keyboard[0][0]
        assert first_button.text == "📱 Mini App"
        assert first_button.web_app is not None
        assert first_button.web_app.url == miniapp_url

    def test_main_menu_with_admin_without_miniapp(self):
        """Test admin menu without miniapp URL."""
        result = MainMenuKeyboard.main_menu_with_admin(
            admin_id=123, current_user_id=123
        )
        
        assert isinstance(result, InlineKeyboardMarkup)
        # Admin row + 3 regular rows
        assert len(result.inline_keyboard) == 4
        assert result.inline_keyboard[0][0].text == "🔧 Admin"

    def test_main_menu_with_admin_with_miniapp(self):
        """Test admin menu with miniapp URL."""
        miniapp_url = "https://app.example.com/miniapp/entry"
        result = MainMenuKeyboard.main_menu_with_admin(
            admin_id=123, current_user_id=123, miniapp_url=miniapp_url
        )
        
        assert isinstance(result, InlineKeyboardMarkup)
        # Admin row + 3 regular rows (first with mini app)
        assert len(result.inline_keyboard) == 4
        # Second row (index 1) should have mini app button first
        second_row = result.inline_keyboard[1]
        assert second_row[0].text == "📱 Mini App"
        assert second_row[0].web_app.url == miniapp_url

    def test_main_menu_with_admin_non_admin_user(self):
        """Test admin menu for non-admin user returns regular menu."""
        miniapp_url = "https://app.example.com/miniapp/entry"
        result = MainMenuKeyboard.main_menu_with_admin(
            admin_id=123, current_user_id=456, miniapp_url=miniapp_url
        )
        
        # Should return regular main menu (not admin)
        assert len(result.inline_keyboard) == 3
        assert result.inline_keyboard[0][0].text == "📱 Mini App"
```

**Step 2: Run tests**

```bash
pytest tests/telegram_bot/keyboards/test_main_menu.py -v
```

**Step 3: Commit tests**

```bash
git add tests/telegram_bot/keyboards/test_main_menu.py
git commit -m "test: add tests for Mini App button in main menu"
```

---

## Task 5: Verify Integration

**Step 1: Check all main menu usages updated**

```bash
grep -r "\.main_menu()" telegram_bot/ --include="*.py" | grep -v "__pycache__"
```

**Step 2: Verify MINIAPP_URL in config**

```bash
grep -A2 "MINIAPP_URL" config.py
```

**Step 3: Run all tests**

```bash
pytest -v
```

**Step 4: Commit if any additional changes**

```bash
git add .
git commit -m "fix: ensure all main menu calls pass miniapp_url"
```

---

## Summary

This plan adds a Mini App button to the Telegram bot's main menu by:
1. Importing `WebAppInfo` from python-telegram-bot
2. Adding `miniapp_url` parameter to `MainMenuKeyboard.main_menu()` and `main_menu_with_admin()`
3. Conditionally displaying the Mini App button when URL is provided
4. Updating handlers to pass the configured `MINIAPP_URL`
5. Adding comprehensive tests for the new functionality
