"""
Tests para keyboards de operaciones.

Author: uSipipo Team
Version: 1.0.0
"""

import pytest

from telegram_bot.features.operations.keyboards_operations import OperationsKeyboards


class TestOperationsKeyboards:
    """Tests para OperationsKeyboards."""

    def test_operations_menu_contains_all_buttons(self):
        """El menú de operaciones debe contener todos los botones principales."""
        keyboard = OperationsKeyboards.operations_menu(credits=100)
        buttons = [btn.text for row in keyboard.inline_keyboard for btn in row]

        assert "🎁 Créditos (100)" in buttons
        assert "👥 Referidos" in buttons
        assert "🛒 Shop" in buttons
        assert "📜 Historial" in buttons
        assert "🔙 Volver" in buttons

    def test_operations_menu_layout(self):
        """El menú debe tener el layout correcto con 2 columnas para botones principales."""
        keyboard = OperationsKeyboards.operations_menu(credits=0)

        # Primera fila: Créditos y Referidos (2 botones)
        assert len(keyboard.inline_keyboard[0]) == 2
        assert "Créditos" in keyboard.inline_keyboard[0][0].text
        assert "Referidos" in keyboard.inline_keyboard[0][1].text

        # Segunda fila: Shop y Historial (2 botones)
        assert len(keyboard.inline_keyboard[1]) == 2
        assert "Shop" in keyboard.inline_keyboard[1][0].text
        assert "Historial" in keyboard.inline_keyboard[1][1].text

        # Tercera fila: Volver (1 botón)
        assert len(keyboard.inline_keyboard[2]) == 1

    def test_transactions_history_menu_basic(self):
        """El menú de historial debe tener botón de volver."""
        keyboard = OperationsKeyboards.transactions_history_menu()
        buttons = [btn.text for row in keyboard.inline_keyboard for btn in row]

        assert "🔙 Volver a Operaciones" in buttons

    def test_transactions_history_menu_with_pagination(self):
        """El menú de historial debe mostrar botones de paginación cuando corresponde."""
        # Página 0 con más páginas
        keyboard = OperationsKeyboards.transactions_history_menu(has_more=True, page=0)
        buttons = [btn.text for row in keyboard.inline_keyboard for btn in row]

        assert "Siguiente ▶️" in buttons
        assert "🔙 Volver a Operaciones" in buttons

        # Página 1+ con más páginas
        keyboard = OperationsKeyboards.transactions_history_menu(has_more=True, page=1)
        buttons = [btn.text for row in keyboard.inline_keyboard for btn in row]

        assert "◀️ Anterior" in buttons
        assert "Siguiente ▶️" in buttons
        assert "🔙 Volver a Operaciones" in buttons

        # Última página (sin más)
        keyboard = OperationsKeyboards.transactions_history_menu(has_more=False, page=2)
        buttons = [btn.text for row in keyboard.inline_keyboard for btn in row]

        assert "◀️ Anterior" in buttons
        assert "Siguiente ▶️" not in buttons

    def test_transactions_history_menu_pagination_callbacks(self):
        """Los botones de paginación deben tener los callback_data correctos."""
        keyboard = OperationsKeyboards.transactions_history_menu(has_more=True, page=2)

        # Buscar botón anterior
        prev_button = None
        for row in keyboard.inline_keyboard:
            for btn in row:
                if "Anterior" in btn.text:
                    prev_button = btn
                    break

        assert prev_button is not None
        assert prev_button.callback_data == "transactions_page_1"

    def test_credits_menu(self):
        """El menú de créditos debe tener los botones correctos."""
        keyboard = OperationsKeyboards.credits_menu(credits=50)
        buttons = [btn.text for row in keyboard.inline_keyboard for btn in row]

        assert "✨ Canjear por GB" in buttons
        assert "🔑 Canjear por Slot" in buttons
        assert "🔙 Volver" in buttons

    def test_shop_menu(self):
        """El menú de shop debe tener los botones correctos."""
        keyboard = OperationsKeyboards.shop_menu()
        buttons = [btn.text for row in keyboard.inline_keyboard for btn in row]

        assert "📦 Paquetes de GB" in buttons
        assert "🔑 Slots Adicionales" in buttons
        assert "✨ Extras con Creditos" in buttons
        assert "🔙 Volver" in buttons
