"""
Handlers for VPN key deletion operations.

Author: uSipipo Team
Version: 1.0.0 - Key Deletion
"""

from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.common.decorators import admin_required
from utils.logger import logger
from utils.spinner import SpinnerManager, admin_spinner_callback

from .keyboards_admin_vpn import AdminVpnKeyboards
from .messages_admin_vpn import AdminVpnMessages


class KeyDeletionMixin:
    """Mixin for key deletion operations."""

    @admin_required
    async def confirm_delete_key(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Show confirmation for key deletion."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return None

        parts = query.data.split("_")
        key_type = parts[-2]
        key_id_short = parts[-1]

        try:
            keys = await self.vpn_service.list_server_keys(
                key_type, include_inactive=True
            )
            key = next(
                (k for k in keys if str(k.get("id", "")).startswith(key_id_short)), None
            )
            if not key:
                await self._safe_edit_message(
                    query,
                    context,
                    text=AdminVpnMessages.ERROR_KEY_NOT_FOUND,
                    reply_markup=AdminVpnKeyboards.back_to_server(key_type),
                    parse_mode="Markdown",
                )
                return None
            full_key_id = str(key.get("id", ""))
            message = AdminVpnMessages.CONFIRM_DELETE_KEY.format(key_id=key_id_short)

            await self._safe_edit_message(
                query,
                context,
                text=message,
                reply_markup=AdminVpnKeyboards.confirmation(
                    "delete", full_key_id, key_type
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Error confirming delete: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=AdminVpnMessages.ERROR_OPERATION_FAILED.format(error=str(e)),
                reply_markup=AdminVpnKeyboards.back_to_server(key_type),
                parse_mode="Markdown",
            )
        return None

    @admin_required
    @admin_spinner_callback
    async def execute_delete_key(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: Optional[int] = None,
    ):
        """Execute key deletion."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return None

        parts = query.data.split("_")
        key_type = parts[-2]
        key_id_short = parts[-1]

        try:
            keys = await self.vpn_service.list_server_keys(
                key_type, include_inactive=True
            )
            key = next(
                (k for k in keys if str(k.get("id", "")).startswith(key_id_short)), None
            )
            if not key:
                await SpinnerManager.replace_spinner_with_message(
                    update,
                    context,
                    spinner_message_id,
                    text=AdminVpnMessages.ERROR_KEY_NOT_FOUND,
                    reply_markup=AdminVpnKeyboards.back_to_server(key_type),
                    parse_mode="Markdown",
                )
                return None
            full_key_id = str(key.get("id", ""))
            result = await self.vpn_service.delete_key_complete(full_key_id, key_type)

            if result.get("success"):
                message = AdminVpnMessages.KEY_DELETED
            else:
                error = result.get("error", "Error desconocido")
                message = AdminVpnMessages.ERROR_OPERATION_FAILED.format(error=error)

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminVpnKeyboards.back_to_server(key_type),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error deleting key: {e}")
            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=AdminVpnMessages.ERROR_OPERATION_FAILED.format(error=str(e)),
                reply_markup=AdminVpnKeyboards.back_to_server(key_type),
                parse_mode="Markdown",
            )

        return None

    @admin_required
    async def cancel_key_action(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Cancel key action."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return None

        parts = query.data.split("_")
        key_type = parts[-2]

        await self._safe_edit_message(
            query,
            context,
            text=AdminVpnMessages.OPERATION_CANCELLED,
            reply_markup=AdminVpnKeyboards.back_to_server(key_type),
            parse_mode="Markdown",
        )
        return None
