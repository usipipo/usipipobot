"""
Tests para los handlers de tickets administrativos.

Issue: #251 - Botones del menú de gestión de tickets admin no funcionan
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update, User, CallbackQuery, Message
from telegram.ext import ContextTypes

from domain.entities.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from telegram_bot.features.admin.handlers_admin import AdminHandler, VIEWING_TICKETS


@pytest.fixture
def mock_admin_service():
    """Mock del servicio de admin."""
    service = MagicMock()
    service.ticket_repo = MagicMock()
    return service


@pytest.fixture
def admin_handler(mock_admin_service):
    """Instancia del handler de admin."""
    return AdminHandler(mock_admin_service)


@pytest.fixture
def mock_update():
    """Mock de update de Telegram."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123456789
    update.callback_query = None
    update.message = None
    return update


@pytest.fixture
def mock_context():
    """Mock del contexto."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    return context


# Patch settings at module level for all tests
@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings para todos los tests."""
    with patch('config.settings') as mock_settings:
        mock_settings.ADMIN_ID = "123456789"
        mock_settings.MINIAPP_URL = "https://example.com"
        yield mock_settings


class TestShowTicketsMenu:
    """Tests para mostrar el menú de tickets."""

    @pytest.mark.asyncio
    async def test_show_tickets_menu(self, admin_handler, mock_update, mock_context, mock_settings):
        """Test que el menú de tickets se muestra correctamente."""
        mock_query = MagicMock(spec=CallbackQuery)
        mock_query.data = "admin_tickets_menu"
        mock_update.callback_query = mock_query

        with patch('application.services.ticket_service.TicketService') as mock_ticket_service:
            mock_service_instance = MagicMock()
            mock_service_instance.count_open_tickets = AsyncMock(return_value=5)
            mock_ticket_service.return_value = mock_service_instance

            result = await admin_handler.show_tickets_menu(mock_update, mock_context)

            assert result == VIEWING_TICKETS
            mock_query.answer.assert_called_once()


class TestShowOpenTickets:
    """Tests para mostrar tickets abiertos."""

    @pytest.mark.asyncio
    async def test_show_open_tickets_empty(self, admin_handler, mock_update, mock_context, mock_settings):
        """Test mostrar tickets abiertos cuando no hay ninguno."""
        mock_query = MagicMock(spec=CallbackQuery)
        mock_query.data = "admin_tickets_open"
        mock_update.callback_query = mock_query

        with patch('application.services.ticket_service.TicketService') as mock_ticket_service:
            mock_service_instance = MagicMock()
            mock_service_instance.get_pending_tickets = AsyncMock(return_value=[])
            mock_ticket_service.return_value = mock_service_instance

            result = await admin_handler.show_open_tickets(mock_update, mock_context)

            assert result == VIEWING_TICKETS

    @pytest.mark.asyncio
    async def test_show_open_tickets_with_data(self, admin_handler, mock_update, mock_context, mock_settings):
        """Test mostrar tickets abiertos con tickets pendientes."""
        mock_query = MagicMock(spec=CallbackQuery)
        mock_query.data = "admin_tickets_open"
        mock_update.callback_query = mock_query

        tickets = [
            Ticket(
                user_id=123,
                category=TicketCategory.VPN_FAIL,
                priority=TicketPriority.HIGH,
                subject="Test ticket",
                id=uuid.uuid4(),
                status=TicketStatus.OPEN,
                created_at=datetime.now(timezone.utc),
            )
        ]

        with patch('application.services.ticket_service.TicketService') as mock_ticket_service:
            mock_service_instance = MagicMock()
            mock_service_instance.get_pending_tickets = AsyncMock(return_value=tickets)
            mock_ticket_service.return_value = mock_service_instance

            result = await admin_handler.show_open_tickets(mock_update, mock_context)

            assert result == VIEWING_TICKETS


class TestTicketReply:
    """Tests para responder a tickets."""

    @pytest.mark.asyncio
    async def test_start_ticket_reply(self, admin_handler, mock_update, mock_context, mock_settings):
        """Test iniciar respuesta a un ticket."""
        mock_query = MagicMock(spec=CallbackQuery)
        mock_query.data = "admin_ticket_resp_12345"
        mock_update.callback_query = mock_query

        result = await admin_handler.start_ticket_reply(mock_update, mock_context)

        assert result == VIEWING_TICKETS
        assert mock_context.user_data.get("admin_replying_ticket_id") == 12345

    @pytest.mark.asyncio
    async def test_send_ticket_reply_valid(self, admin_handler, mock_update, mock_context, mock_settings):
        """Test enviar respuesta válida a un ticket."""
        mock_message = MagicMock(spec=Message)
        mock_message.text = "Esta es una respuesta válida al ticket"
        mock_update.message = mock_message
        mock_context.user_data = {"admin_replying_ticket_id": 12345}

        result = await admin_handler.send_ticket_reply(mock_update, mock_context)

        assert result == VIEWING_TICKETS
        assert "admin_replying_ticket_id" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_send_ticket_reply_too_short(self, admin_handler, mock_update, mock_context, mock_settings):
        """Test enviar respuesta muy corta."""
        mock_message = MagicMock(spec=Message)
        mock_message.text = "Hi"
        mock_update.message = mock_message
        mock_context.user_data = {"admin_replying_ticket_id": 12345}

        result = await admin_handler.send_ticket_reply(mock_update, mock_context)

        assert result == VIEWING_TICKETS  # Returns to same state to retry


class TestCloseAndReopenTicket:
    """Tests para cerrar y reabrir tickets."""

    @pytest.mark.asyncio
    async def test_close_admin_ticket(self, admin_handler, mock_update, mock_context, mock_settings):
        """Test cerrar un ticket desde admin."""
        mock_query = MagicMock(spec=CallbackQuery)
        mock_query.data = "admin_ticket_close_12345"
        mock_update.callback_query = mock_query

        result = await admin_handler.close_admin_ticket(mock_update, mock_context)

        assert result == VIEWING_TICKETS

    @pytest.mark.asyncio
    async def test_reopen_admin_ticket(self, admin_handler, mock_update, mock_context, mock_settings):
        """Test reabrir un ticket desde admin."""
        mock_query = MagicMock(spec=CallbackQuery)
        mock_query.data = "admin_ticket_reopen_12345"
        mock_update.callback_query = mock_query

        result = await admin_handler.reopen_admin_ticket(mock_update, mock_context)

        assert result == VIEWING_TICKETS


class TestCategoryFilter:
    """Tests para filtrar tickets por categoría."""

    @pytest.mark.asyncio
    async def test_show_category_filter(self, admin_handler, mock_update, mock_context, mock_settings):
        """Test mostrar menú de filtro por categoría."""
        mock_query = MagicMock(spec=CallbackQuery)
        mock_query.data = "admin_tickets_filter"
        mock_update.callback_query = mock_query

        result = await admin_handler.show_category_filter(mock_update, mock_context)

        assert result == VIEWING_TICKETS

    @pytest.mark.asyncio
    async def test_filter_by_vpn_category(self, admin_handler, mock_update, mock_context, mock_settings):
        """Test filtrar tickets por categoría VPN."""
        mock_query = MagicMock(spec=CallbackQuery)
        mock_query.data = "admin_tickets_filter_vpn"
        mock_update.callback_query = mock_query

        with patch('application.services.ticket_service.TicketService') as mock_ticket_service:
            mock_service_instance = MagicMock()
            mock_service_instance.get_tickets_by_category = AsyncMock(return_value=[])
            mock_ticket_service.return_value = mock_service_instance

            result = await admin_handler.filter_tickets_by_category(mock_update, mock_context)

            assert result == VIEWING_TICKETS


class TestViewAdminTicket:
    """Tests para ver detalle de un ticket."""

    @pytest.mark.asyncio
    async def test_view_admin_ticket_not_found(self, admin_handler, mock_update, mock_context, mock_settings):
        """Test ver ticket que no existe."""
        mock_query = MagicMock(spec=CallbackQuery)
        mock_query.data = f"admin_ticket_{uuid.uuid4()}"
        mock_update.callback_query = mock_query

        with patch('application.services.ticket_service.TicketService') as mock_ticket_service:
            mock_service_instance = MagicMock()
            mock_service_instance.get_ticket_with_messages = AsyncMock(return_value=None)
            mock_ticket_service.return_value = mock_service_instance

            result = await admin_handler.view_admin_ticket(mock_update, mock_context)

            assert result == VIEWING_TICKETS

    @pytest.mark.asyncio
    async def test_view_admin_ticket_success(self, admin_handler, mock_update, mock_context, mock_settings):
        """Test ver ticket existente."""
        ticket_id = uuid.uuid4()
        mock_query = MagicMock(spec=CallbackQuery)
        mock_query.data = f"admin_ticket_{ticket_id}"
        mock_update.callback_query = mock_query

        ticket = Ticket(
            user_id=123,
            category=TicketCategory.VPN_FAIL,
            priority=TicketPriority.HIGH,
            subject="Test ticket",
            id=ticket_id,
            status=TicketStatus.OPEN,
            created_at=datetime.now(timezone.utc),
        )

        with patch('application.services.ticket_service.TicketService') as mock_ticket_service:
            mock_service_instance = MagicMock()
            mock_service_instance.get_ticket_with_messages = AsyncMock(
                return_value=(ticket, [])
            )
            mock_ticket_service.return_value = mock_service_instance

            result = await admin_handler.view_admin_ticket(mock_update, mock_context)

            assert result == VIEWING_TICKETS
