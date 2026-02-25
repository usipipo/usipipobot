"""
Tests para el flujo de tickets del panel administrativo.

Author: uSipipo Team
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from application.services.admin_service import AdminService
from application.services.ticket_service import TicketService
from domain.entities.ticket import Ticket, TicketStatus, TicketPriority
from telegram_bot.features.admin.handlers_admin import (
    ADMIN_MENU,
    VIEWING_TICKETS,
    VIEWING_TICKET_DETAILS,
    AWAITING_TICKET_RESPONSE,
    AdminHandler,
)


ADMIN_ID = 123456789


@pytest.fixture
def admin_service():
    service = MagicMock(spec=AdminService)
    service.get_users_paginated = AsyncMock(return_value={"users": [], "total_pages": 1, "total_users": 0})
    service.get_user_by_id = AsyncMock(return_value=None)
    service.get_all_keys = AsyncMock(return_value=[])
    service.get_dashboard_stats = AsyncMock(return_value={})
    return service


@pytest.fixture
def ticket_service():
    service = MagicMock(spec=TicketService)
    service.get_all_open_tickets = AsyncMock(return_value=[])
    service.get_ticket = AsyncMock(return_value=None)
    service.respond_to_ticket = AsyncMock(return_value=None)
    service.set_in_progress = AsyncMock(return_value=None)
    return service


@pytest.fixture
def sample_ticket():
    return Ticket(
        id=uuid.uuid4(),
        user_id=123456789,
        subject="Test Subject",
        message="Test message content",
        status=TicketStatus.OPEN,
        priority=TicketPriority.MEDIUM,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def handler(admin_service, ticket_service):
    return AdminHandler(admin_service, ticket_service)


@pytest.fixture
def mock_settings():
    with patch("config.settings") as mock:
        mock.ADMIN_ID = str(ADMIN_ID)
        yield mock


class TestAdminTicketFlow:
    """Tests para el flujo de tickets en el panel admin."""

    @pytest.mark.asyncio
    async def test_show_tickets_empty(self, handler, ticket_service, mock_settings):
        """show_tickets debe mostrar mensaje cuando no hay tickets."""
        ticket_service.get_all_open_tickets = AsyncMock(return_value=[])

        update = MagicMock()
        update.effective_user.id = ADMIN_ID
        update.callback_query = MagicMock()
        update.callback_query.data = "admin_tickets"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.message = None

        context = MagicMock()
        context.user_data = {}

        result = await handler.show_tickets(update, context, spinner_message_id=None)

        assert result == ADMIN_MENU
        ticket_service.get_all_open_tickets.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_tickets_with_tickets(self, handler, ticket_service, sample_ticket, mock_settings):
        """show_tickets debe mostrar lista de tickets pendientes."""
        ticket_service.get_all_open_tickets = AsyncMock(return_value=[sample_ticket])

        update = MagicMock()
        update.effective_user.id = ADMIN_ID
        update.callback_query = MagicMock()
        update.callback_query.data = "admin_tickets"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.message = None

        context = MagicMock()
        context.user_data = {}

        result = await handler.show_tickets(update, context, spinner_message_id=None)

        assert result == VIEWING_TICKETS
        ticket_service.get_all_open_tickets.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_view_ticket(self, handler, ticket_service, sample_ticket, mock_settings):
        """admin_view_ticket debe mostrar detalles del ticket."""
        ticket_service.get_ticket = AsyncMock(return_value=sample_ticket)

        update = MagicMock()
        update.effective_user.id = ADMIN_ID
        update.callback_query = MagicMock()
        update.callback_query.data = f"admin_view_ticket_{sample_ticket.id}"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.message = None

        context = MagicMock()
        context.user_data = {}

        result = await handler.admin_view_ticket(update, context, spinner_message_id=None)

        assert result == VIEWING_TICKET_DETAILS
        ticket_service.get_ticket.assert_called_once()
        assert context.user_data.get("viewing_ticket_id") == str(sample_ticket.id)

    @pytest.mark.asyncio
    async def test_admin_view_ticket_not_found(self, handler, ticket_service, mock_settings):
        """admin_view_ticket debe manejar ticket no encontrado."""
        ticket_service.get_ticket = AsyncMock(return_value=None)

        ticket_id = uuid.uuid4()
        update = MagicMock()
        update.effective_user.id = ADMIN_ID
        update.callback_query = MagicMock()
        update.callback_query.data = f"admin_view_ticket_{ticket_id}"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.message = None

        context = MagicMock()
        context.user_data = {}

        result = await handler.admin_view_ticket(update, context, spinner_message_id=None)

        assert result == ADMIN_MENU

    @pytest.mark.asyncio
    async def test_admin_respond_prompt(self, handler, ticket_service, sample_ticket, mock_settings):
        """admin_respond_prompt debe preparar el estado para responder."""
        update = MagicMock()
        update.effective_user.id = ADMIN_ID
        update.callback_query = MagicMock()
        update.callback_query.data = f"ticket_respond_{sample_ticket.id}"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.message = None

        context = MagicMock()
        context.user_data = {}

        result = await handler.admin_respond_prompt(update, context)

        assert result == AWAITING_TICKET_RESPONSE
        assert context.user_data.get("responding_to_ticket") == str(sample_ticket.id)

    @pytest.mark.asyncio
    async def test_handle_admin_response(self, handler, ticket_service, sample_ticket):
        """handle_admin_response debe guardar la respuesta del admin."""
        ticket_service.respond_to_ticket = AsyncMock(return_value=sample_ticket)
        ticket_service.get_all_open_tickets = AsyncMock(return_value=[])

        update = MagicMock()
        update.effective_user.id = ADMIN_ID
        update.message = MagicMock()
        update.message.text = "Esta es mi respuesta al ticket."
        update.message.reply_text = AsyncMock()
        update.callback_query = None

        context = MagicMock()
        context.user_data = {"responding_to_ticket": str(sample_ticket.id)}

        with patch("telegram_bot.features.admin.handlers_admin.settings") as mock_settings:
            mock_settings.ADMIN_ID = str(ADMIN_ID)
            result = await handler.handle_admin_response(update, context)

        assert result == ADMIN_MENU
        ticket_service.respond_to_ticket.assert_called_once()
        assert context.user_data.get("responding_to_ticket") is None

    @pytest.mark.asyncio
    async def test_handle_admin_response_shows_next_ticket(self, handler, ticket_service, sample_ticket):
        """handle_admin_response debe mostrar tickets restantes después de responder."""
        another_ticket = Ticket(
            id=uuid.uuid4(),
            user_id=987654321,
            subject="Another Ticket",
            message="Another message",
            status=TicketStatus.OPEN,
            priority=TicketPriority.HIGH,
            created_at=datetime.now(timezone.utc),
        )
        ticket_service.respond_to_ticket = AsyncMock(return_value=sample_ticket)
        ticket_service.get_all_open_tickets = AsyncMock(return_value=[another_ticket])

        update = MagicMock()
        update.effective_user.id = ADMIN_ID
        update.message = MagicMock()
        update.message.text = "Respuesta del admin."
        update.message.reply_text = AsyncMock()
        update.callback_query = None

        context = MagicMock()
        context.user_data = {"responding_to_ticket": str(sample_ticket.id)}

        with patch("telegram_bot.features.admin.handlers_admin.settings") as mock_settings:
            mock_settings.ADMIN_ID = str(ADMIN_ID)
            result = await handler.handle_admin_response(update, context)

        assert result == VIEWING_TICKETS

    @pytest.mark.asyncio
    async def test_cancel_admin_response(self, handler, mock_settings):
        """cancel_admin_response debe limpiar el estado y volver al menú."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.message = None

        context = MagicMock()
        context.user_data = {"responding_to_ticket": "some-ticket-id"}

        result = await handler.cancel_admin_response(update, context)

        assert result == ADMIN_MENU
        assert context.user_data.get("responding_to_ticket") is None

    @pytest.mark.asyncio
    async def test_ticket_set_in_progress(self, handler, ticket_service, sample_ticket, mock_settings):
        """ticket_set_in_progress debe cambiar el estado del ticket a in_progress."""
        sample_ticket.status = TicketStatus.IN_PROGRESS
        ticket_service.set_in_progress = AsyncMock(return_value=sample_ticket)
        ticket_service.get_ticket = AsyncMock(return_value=sample_ticket)

        update = MagicMock()
        update.effective_user.id = ADMIN_ID
        update.callback_query = MagicMock()
        update.callback_query.data = f"ticket_progress_{sample_ticket.id}"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.message = None

        context = MagicMock()
        context.user_data = {}

        result = await handler.ticket_set_in_progress(update, context)

        assert result == VIEWING_TICKET_DETAILS
        ticket_service.set_in_progress.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_view_ticket_invalid_uuid(self, handler, mock_settings):
        """admin_view_ticket debe manejar UUID inválido."""
        update = MagicMock()
        update.effective_user.id = ADMIN_ID
        update.callback_query = MagicMock()
        update.callback_query.data = "admin_view_ticket_invalid-uuid"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.message = None

        context = MagicMock()
        context.user_data = {}

        result = await handler.admin_view_ticket(update, context, spinner_message_id=None)

        assert result == ADMIN_MENU

    @pytest.mark.asyncio
    async def test_admin_view_ticket_without_ticket_service(self, admin_service, mock_settings):
        """admin_view_ticket debe manejar cuando no hay ticket_service."""
        handler = AdminHandler(admin_service, ticket_service=None)

        ticket_id = uuid.uuid4()
        update = MagicMock()
        update.effective_user.id = ADMIN_ID
        update.callback_query = MagicMock()
        update.callback_query.data = f"admin_view_ticket_{ticket_id}"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.message = None

        context = MagicMock()
        context.user_data = {}

        result = await handler.admin_view_ticket(update, context, spinner_message_id=None)

        assert result == ADMIN_MENU

    @pytest.mark.asyncio
    async def test_handle_admin_response_non_admin(self, handler, ticket_service, sample_ticket, mock_settings):
        """handle_admin_response debe rechazar usuarios no admin."""
        update = MagicMock()
        update.effective_user.id = 999999999
        update.message = MagicMock()
        update.message.text = "Respuesta no autorizada."
        update.message.reply_text = AsyncMock()
        update.callback_query = None

        context = MagicMock()
        context.user_data = {"responding_to_ticket": str(sample_ticket.id)}

        result = await handler.handle_admin_response(update, context)

        assert result == ADMIN_MENU
        ticket_service.respond_to_ticket.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_admin_response_without_user_data(self, handler, ticket_service, mock_settings):
        """handle_admin_response debe manejar falta de user_data."""
        update = MagicMock()
        update.effective_user.id = ADMIN_ID
        update.message = MagicMock()
        update.message.text = "Respuesta."
        update.callback_query = None

        context = MagicMock()
        context.user_data = None

        result = await handler.handle_admin_response(update, context)

        assert result == ADMIN_MENU
