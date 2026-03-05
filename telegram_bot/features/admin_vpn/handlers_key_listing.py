"""
Handlers for VPN key listing and pagination.

Author: uSipipo Team
Version: 1.0.0 - Key Listing
"""

from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.common.decorators import admin_required
from utils.logger import logger
from utils.spinner import SpinnerManager, admin_spinner_callback

from .keyboards_admin_vpn import AdminVpnKeyboards
from .messages_admin_vpn import AdminVpnMessages

KEYS_PER_PAGE = 10


class KeyListingMixin:
    """Mixin for key listing and pagination operations."""

    @admin_required
    @admin_spinner_callback
    async def list_server_keys(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: Optional[int] = None,
    ):
        """List keys with pagination."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return None

        server_type = query.data.replace("vpn_list_keys_", "")

        if context.user_data is not None:
            context.user_data["vpn_keys_page"] = 1
            context.user_data["vpn_server_type"] = server_type

        try:
            keys = await self.vpn_service.list_server_keys(
                server_type, include_inactive=True
            )

            if not keys:
                await SpinnerManager.replace_spinner_with_message(
                    update,
                    context,
                    spinner_message_id,
                    text=AdminVpnMessages.NO_KEYS.format(
                        server_type=server_type.upper()
                    ),
                    reply_markup=AdminVpnKeyboards.back_to_server(server_type),
                    parse_mode="Markdown",
                )
                return None

            page = 1
            total_pages = max(1, (len(keys) + KEYS_PER_PAGE - 1) // KEYS_PER_PAGE)
            offset = (page - 1) * KEYS_PER_PAGE
            page_keys = keys[offset : offset + KEYS_PER_PAGE]

            active_count = sum(1 for k in keys if k.get("is_active", False))
            inactive_count = len(keys) - active_count

            message = AdminVpnMessages.KEYS_LIST_HEADER.format(
                server_type=server_type.upper()
            )
            message += f"📊 Total: {len(keys)} claves"
            if inactive_count > 0:
                message += (
                    f" (✅ {active_count} activas, ⏸️ {inactive_count} inactivas)"
                )
            message += "\n\n"

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminVpnKeyboards.keys_list_paginated(
                    page_keys, page, total_pages, server_type
                ),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error listing server keys: {e}")
            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=AdminVpnMessages.ERROR_OPERATION_FAILED.format(error=str(e)),
                reply_markup=AdminVpnKeyboards.back_to_server(server_type),
                parse_mode="Markdown",
            )

        return None

    @admin_required
    async def keys_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Navigate between key pages."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return None

        parts = query.data.split("_")
        server_type = parts[-2]
        page = int(parts[-1])

        if context.user_data is not None:
            context.user_data["vpn_keys_page"] = page

        try:
            keys = await self.vpn_service.list_server_keys(
                server_type, include_inactive=True
            )

            if not keys:
                await self._safe_edit_message(
                    query,
                    context,
                    text=AdminVpnMessages.NO_KEYS.format(
                        server_type=server_type.upper()
                    ),
                    reply_markup=AdminVpnKeyboards.back_to_server(server_type),
                    parse_mode="Markdown",
                )
                return None

            total_pages = max(1, (len(keys) + KEYS_PER_PAGE - 1) // KEYS_PER_PAGE)
            offset = (page - 1) * KEYS_PER_PAGE
            page_keys = keys[offset : offset + KEYS_PER_PAGE]

            active_count = sum(1 for k in keys if k.get("is_active", False))
            inactive_count = len(keys) - active_count

            message = AdminVpnMessages.KEYS_LIST_HEADER.format(
                server_type=server_type.upper()
            )
            message += f"📊 Total: {len(keys)} claves"
            if inactive_count > 0:
                message += (
                    f" (✅ {active_count} activas, ⏸️ {inactive_count} inactivas)"
                )
            message += "\n\n"

            await self._safe_edit_message(
                query,
                context,
                text=message,
                reply_markup=AdminVpnKeyboards.keys_list_paginated(
                    page_keys, page, total_pages, server_type
                ),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error navigating keys page: {e}")
            await self._handle_error(update, context, e, "keys_page")

        return None
