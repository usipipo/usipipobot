"""
Tests para handlers de operaciones.

Author: uSipipo Team
Version: 1.0.0
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from telegram import Update, User
from telegram.ext import ContextTypes

from domain.entities.crypto_order import CryptoOrder, CryptoOrderStatus
from telegram_bot.features.operations.handlers_operations import OperationsHandler


@pytest.fixture
def mock_vpn_service():
    return MagicMock()


@pytest.fixture
def mock_referral_service():
    service = MagicMock()
    service.get_referral_stats = AsyncMock(return_value=MagicMock(referral_credits=100))
    return service


@pytest.fixture
def mock_crypto_order_repo():
    repo = MagicMock()
    repo.get_by_user_paginated = AsyncMock(return_value=[])
    repo.count_by_user = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def handler(mock_vpn_service, mock_referral_service, mock_crypto_order_repo):
    return OperationsHandler(
        vpn_service=mock_vpn_service,
        referral_service=mock_referral_service,
        crypto_order_repo=mock_crypto_order_repo,
    )


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123456
    update.callback_query = MagicMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.data = "transactions_history"
    return update


@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    return context


class TestShowTransactionsHistory:
    """Tests para show_transactions_history."""

    @pytest.mark.asyncio
    async def test_show_transactions_history_no_orders(
        self, handler, mock_update, mock_context, mock_crypto_order_repo
    ):
        """Mostrar mensaje cuando no hay transacciones."""
        mock_crypto_order_repo.get_by_user_paginated.return_value = []

        with patch(
            "telegram_bot.features.operations.handlers_operations.TelegramUtils"
        ) as mock_utils:
            mock_utils.safe_edit_message = AsyncMock()
            await handler.show_transactions_history(mock_update, mock_context)

            # Verificar que se llamó a safe_edit_message
            mock_utils.safe_edit_message.assert_called_once()
            # Verificar que el mensaje contiene información sobre no tener transacciones
            call_args = mock_utils.safe_edit_message.call_args
            assert (
                "Sin Transacciones" in call_args.kwargs["text"] or "📭" in call_args.kwargs["text"]
            )

    @pytest.mark.asyncio
    async def test_show_transactions_history_with_orders(
        self, handler, mock_update, mock_context, mock_crypto_order_repo
    ):
        """Mostrar lista de transacciones cuando existen órdenes."""
        # Crear órdenes de prueba
        orders = [
            CryptoOrder(
                id=uuid4(),
                user_id=123456,
                package_type="basic",
                amount_usdt=10.0,
                wallet_address="TEST123",
                status=CryptoOrderStatus.COMPLETED,
                created_at=datetime.now(timezone.utc),
            ),
            CryptoOrder(
                id=uuid4(),
                user_id=123456,
                package_type="premium",
                amount_usdt=25.0,
                wallet_address="TEST456",
                status=CryptoOrderStatus.PENDING,
                created_at=datetime.now(timezone.utc),
            ),
        ]
        mock_crypto_order_repo.get_by_user_paginated.return_value = orders

        with patch(
            "telegram_bot.features.operations.handlers_operations.TelegramUtils"
        ) as mock_utils:
            mock_utils.safe_edit_message = AsyncMock()
            await handler.show_transactions_history(mock_update, mock_context)

            mock_utils.safe_edit_message.assert_called_once()
            call_args = mock_utils.safe_edit_message.call_args
            text = call_args.kwargs["text"]

            # Verificar que el mensaje contiene información de las órdenes
            assert "Historial" in text
            assert "BASIC" in text or "PREMIUM" in text
            assert "10.0" in text or "25.0" in text

    @pytest.mark.asyncio
    async def test_show_transactions_history_with_pagination(
        self, handler, mock_update, mock_context, mock_crypto_order_repo
    ):
        """Mostrar paginación cuando hay más de 10 órdenes."""
        # Crear 12 órdenes (más del límite de 10)
        orders = [
            CryptoOrder(
                id=uuid4(),
                user_id=123456,
                package_type="basic",
                amount_usdt=10.0,
                wallet_address=f"TEST{i}",
                status=CryptoOrderStatus.COMPLETED,
                created_at=datetime.now(timezone.utc),
            )
            for i in range(12)
        ]
        mock_crypto_order_repo.get_by_user_paginated.return_value = orders

        with patch(
            "telegram_bot.features.operations.handlers_operations.TelegramUtils"
        ) as mock_utils:
            mock_utils.safe_edit_message = AsyncMock()
            await handler.show_transactions_history(mock_update, mock_context)

            mock_utils.safe_edit_message.assert_called_once()
            call_args = mock_utils.safe_edit_message.call_args
            keyboard = call_args.kwargs["reply_markup"]

            # Verificar que hay botones de paginación
            button_texts = [btn.text for row in keyboard.inline_keyboard for btn in row]
            assert any("Siguiente" in text for text in button_texts)

    @pytest.mark.asyncio
    async def test_show_transactions_history_no_repo(self, handler, mock_update, mock_context):
        """Manejar error cuando no hay repositorio disponible."""
        handler.crypto_order_repo = None

        with patch(
            "telegram_bot.features.operations.handlers_operations.TelegramUtils"
        ) as mock_utils:
            mock_utils.safe_edit_message = AsyncMock()
            await handler.show_transactions_history(mock_update, mock_context)

            mock_utils.safe_edit_message.assert_called_once()
            call_args = mock_utils.safe_edit_message.call_args
            assert "Error" in call_args.kwargs["text"] or "SYSTEM_ERROR" in str(
                call_args.kwargs["text"]
            )


class TestFormatOrdersList:
    """Tests para _format_orders_list."""

    def test_format_orders_list_empty(self, handler):
        """Formatear lista vacía devuelve footer con totales en cero."""
        result = handler._format_orders_list([])
        assert "Total: 0.0 USDT" in result
        assert "0 transacciones" in result

    def test_format_orders_list_with_completed(self, handler):
        """Formatear orden completada muestra emoji correcto."""
        orders = [
            CryptoOrder(
                id=uuid4(),
                user_id=123456,
                package_type="basic",
                amount_usdt=10.0,
                wallet_address="TEST",
                status=CryptoOrderStatus.COMPLETED,
                created_at=datetime.now(timezone.utc),
            )
        ]
        result = handler._format_orders_list(orders)

        assert "🟢" in result
        assert "✅" in result
        assert "BASIC" in result
        assert "10.0" in result
        assert "Completada" in result

    def test_format_orders_list_with_pending(self, handler):
        """Formatear orden pendiente muestra emoji correcto."""
        orders = [
            CryptoOrder(
                id=uuid4(),
                user_id=123456,
                package_type="premium",
                amount_usdt=25.0,
                wallet_address="TEST",
                status=CryptoOrderStatus.PENDING,
                created_at=datetime.now(timezone.utc),
            )
        ]
        result = handler._format_orders_list(orders)

        assert "🟡" in result
        assert "⏳" in result
        assert "PREMIUM" in result
        assert "25.0" in result
        assert "Pendiente" in result

    def test_format_orders_list_with_failed(self, handler):
        """Formatear orden fallida muestra emoji correcto."""
        orders = [
            CryptoOrder(
                id=uuid4(),
                user_id=123456,
                package_type="basic",
                amount_usdt=5.0,
                wallet_address="TEST",
                status=CryptoOrderStatus.FAILED,
                created_at=datetime.now(timezone.utc),
            )
        ]
        result = handler._format_orders_list(orders)

        assert "🔴" in result
        assert "❌" in result
        assert "Fallida" in result

    def test_format_orders_list_with_expired(self, handler):
        """Formatear orden expirada muestra emoji correcto."""
        orders = [
            CryptoOrder(
                id=uuid4(),
                user_id=123456,
                package_type="pro",
                amount_usdt=50.0,
                wallet_address="TEST",
                status=CryptoOrderStatus.EXPIRED,
                created_at=datetime.now(timezone.utc),
            )
        ]
        result = handler._format_orders_list(orders)

        assert "🔴" in result
        assert "⚠️" in result
        assert "PRO" in result
        assert "Expirada" in result


class TestHandleTransactionsPagination:
    """Tests para _handle_transactions_pagination."""

    @pytest.mark.asyncio
    async def test_pagination_next_page(
        self, handler, mock_update, mock_context, mock_crypto_order_repo
    ):
        """Navegar a la siguiente página."""
        mock_update.callback_query.data = "transactions_page_2"
        mock_crypto_order_repo.get_by_user_paginated.return_value = []

        with patch.object(
            handler, "show_transactions_history", new_callable=AsyncMock
        ) as mock_show:
            await handler._handle_transactions_pagination(mock_update, mock_context)

            mock_show.assert_called_once_with(mock_update, mock_context, page=2)

    @pytest.mark.asyncio
    async def test_pagination_previous_page(
        self, handler, mock_update, mock_context, mock_crypto_order_repo
    ):
        """Navegar a la página anterior."""
        mock_update.callback_query.data = "transactions_page_0"
        mock_crypto_order_repo.get_by_user_paginated.return_value = []

        with patch.object(
            handler, "show_transactions_history", new_callable=AsyncMock
        ) as mock_show:
            await handler._handle_transactions_pagination(mock_update, mock_context)

            mock_show.assert_called_once_with(mock_update, mock_context, page=0)

    @pytest.mark.asyncio
    async def test_pagination_invalid_data(self, handler, mock_update, mock_context):
        """Manejar datos de paginación inválidos."""
        mock_update.callback_query.data = "transactions_page_invalid"

        # No debería lanzar excepción
        await handler._handle_transactions_pagination(mock_update, mock_context)
        # El test pasa si no hay excepción
