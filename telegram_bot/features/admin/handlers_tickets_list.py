"""
Handlers para listado de tickets en panel administrativo.

Author: uSipipo Team
Version: 1.0.0 - Refactor from handlers_tickets.py
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from telegram_bot.common.decorators import admin_required
from telegram_bot.features.tickets.keyboards_tickets import TicketKeyboards
from telegram_bot.features.tickets.messages_tickets import TicketMessages
from domain.entities.ticket import TicketCategory
from utils.spinner import SpinnerManager, admin_spinner_callback

ADMIN_MENU = 0
VIEWING_TICKETS = 9


class TicketsListMixin:
    """Mixin para listado de tickets en panel admin."""

    @admin_required
    async def show_tickets_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra el menú de gestión de tickets."""
        query = update.callback_query
        await self._safe_answer_query(query)

        try:
            from application.services.ticket_service import TicketService
            ticket_service = TicketService(self.service.ticket_repo)
            open_count = await ticket_service.count_open_tickets()
        except Exception:
            open_count = 0

        await self._safe_edit_message(
            query,
            context,
            text=TicketMessages.Admin.menu(open_count),
            reply_markup=TicketKeyboards.admin_menu(open_count),
            parse_mode="Markdown",
        )
        return VIEWING_TICKETS

    @admin_required
    @admin_spinner_callback
    async def show_open_tickets(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Muestra tickets abiertos pendientes."""
        query = update.callback_query
        await self._safe_answer_query(query)

        try:
            from application.services.ticket_service import TicketService
            ticket_service = TicketService(self.service.ticket_repo)
            tickets = await ticket_service.get_pending_tickets()

            if not tickets:
                await SpinnerManager.replace_spinner_with_message(
                    update,
                    context,
                    spinner_message_id,
                    text="📭 *No hay tickets abiertos*\n\nTodos los tickets han sido atendidos.",
                    reply_markup=TicketKeyboards.back_to_menu(),
                    parse_mode="Markdown",
                )
                return VIEWING_TICKETS

            message = (
                f"📂 *Tickets Abiertos*\n\n"
                f"Total: {len(tickets)} tickets pendientes\n\n"
                "Selecciona uno para ver detalles:"
            )

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=TicketKeyboards.admin_tickets_list(tickets),
                parse_mode="Markdown",
            )
            return VIEWING_TICKETS

        except Exception as e:
            await self._handle_error(update, context, e, "show_open_tickets")
            return VIEWING_TICKETS

    @admin_required
    @admin_spinner_callback
    async def show_all_tickets(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Muestra todos los tickets."""
        query = update.callback_query
        await self._safe_answer_query(query)

        try:
            from application.services.ticket_service import TicketService
            ticket_service = TicketService(self.service.ticket_repo)

            all_tickets = []
            for category in TicketCategory:
                tickets = await ticket_service.get_tickets_by_category(category)
                all_tickets.extend(tickets)

            all_tickets.sort(key=lambda t: t.created_at, reverse=True)

            if not all_tickets:
                await SpinnerManager.replace_spinner_with_message(
                    update,
                    context,
                    spinner_message_id,
                    text="📭 *No hay tickets*\n\nEl sistema no tiene tickets registrados.",
                    reply_markup=TicketKeyboards.back_to_menu(),
                    parse_mode="Markdown",
                )
                return VIEWING_TICKETS

            message = (
                f"📋 *Todos los Tickets*\n\n"
                f"Total: {len(all_tickets)} tickets\n\n"
                "Selecciona uno para ver detalles:"
            )

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=TicketKeyboards.admin_tickets_list(all_tickets[:10]),
                parse_mode="Markdown",
            )
            return VIEWING_TICKETS

        except Exception as e:
            await self._handle_error(update, context, e, "show_all_tickets")
            return VIEWING_TICKETS

    @admin_required
    async def show_category_filter(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra menú de filtro por categoría."""
        query = update.callback_query
        await self._safe_answer_query(query)

        await self._safe_edit_message(
            query,
            context,
            text="🔍 *Filtrar por Categoría*\n\nSelecciona una categoría:",
            reply_markup=TicketKeyboards.admin_category_filter(),
            parse_mode="Markdown",
        )
        return VIEWING_TICKETS

    @admin_required
    @admin_spinner_callback
    async def filter_tickets_by_category(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Filtra tickets por categoría seleccionada."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return VIEWING_TICKETS

        category_map = {
            "admin_tickets_filter_vpn": TicketCategory.VPN_FAIL,
            "admin_tickets_filter_payment": TicketCategory.PAYMENT,
            "admin_tickets_filter_config": TicketCategory.ACCOUNT,
            "admin_tickets_filter_bug": TicketCategory.VPN_FAIL,
            "admin_tickets_filter_other": TicketCategory.OTHER,
        }

        category = category_map.get(query.data)
        if not category:
            return VIEWING_TICKETS

        try:
            from application.services.ticket_service import TicketService
            ticket_service = TicketService(self.service.ticket_repo)
            tickets = await ticket_service.get_tickets_by_category(category)

            category_names = {
                TicketCategory.VPN_FAIL: "🔌 VPN",
                TicketCategory.PAYMENT: "💳 Pagos",
                TicketCategory.ACCOUNT: "📱 Configuración",
                TicketCategory.OTHER: "❓ Otros",
            }

            if not tickets:
                await SpinnerManager.replace_spinner_with_message(
                    update,
                    context,
                    spinner_message_id,
                    text=f"📭 *No hay tickets en {category_names.get(category, category.value)}*",
                    reply_markup=TicketKeyboards.back_to_menu(),
                    parse_mode="Markdown",
                )
                return VIEWING_TICKETS

            message = (
                f"{category_names.get(category, category.value)} *Tickets*\n\n"
                f"Total: {len(tickets)} tickets\n\n"
                "Selecciona uno para ver detalles:"
            )

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=TicketKeyboards.admin_tickets_list(tickets),
                parse_mode="Markdown",
            )
            return VIEWING_TICKETS

        except Exception as e:
            await self._handle_error(update, context, e, "filter_tickets_by_category")
            return VIEWING_TICKETS
