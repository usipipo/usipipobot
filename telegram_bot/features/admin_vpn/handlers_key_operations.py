"""
Handlers for VPN key operations (details, enable, disable).

Author: uSipipo Team
Version: 1.0.0 - Key Operations
"""

from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.common.decorators import admin_required
from utils.logger import logger
from utils.spinner import SpinnerManager, admin_spinner_callback

from .keyboards_admin_vpn import AdminVpnKeyboards
from .messages_admin_vpn import AdminVpnMessages


class KeyOperationsMixin:
    """Mixin for key operations (details, enable, disable)."""

    @admin_required
    @admin_spinner_callback
    async def show_key_details(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: Optional[int] = None,
    ):
        """Show key details with action buttons."""
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

            last_seen = key.get("last_seen_at") or "Nunca"
            created_at = key.get("created_at") or "N/A"

            full_key_id = str(key.get("id", ""))
            message = AdminVpnMessages.KEY_DETAILS.format(
                key_id=full_key_id[:8],
                name=key.get("name", "N/A"),
                user_id=key.get("user_id", "N/A"),
                key_type=key_type.upper(),
                used_bytes=key.get("used_bytes", 0),
                status="Activa" if key.get("is_active") else "Inactiva",
                last_seen=last_seen,
                created_at=created_at,
            )

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminVpnKeyboards.key_actions(
                    full_key_id, key.get("is_active", False), key_type
                ),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error showing key details: {e}")
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
    @admin_spinner_callback
    async def handle_key_enable(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: Optional[int] = None,
    ):
        """Enable a key."""
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
            result = await self.vpn_service.enable_key(full_key_id, key_type)

            if result.get("success"):
                message = AdminVpnMessages.KEY_ENABLED
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
            logger.error(f"Error enabling key: {e}")
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
    @admin_spinner_callback
    async def handle_key_disable(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: Optional[int] = None,
    ):
        """Disable a key."""
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
            result = await self.vpn_service.disable_key(full_key_id, key_type)

            if result.get("success"):
                message = AdminVpnMessages.KEY_DISABLED
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
            logger.error(f"Error disabling key: {e}")
            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=AdminVpnMessages.ERROR_OPERATION_FAILED.format(error=str(e)),
                reply_markup=AdminVpnKeyboards.back_to_server(key_type),
                parse_mode="Markdown",
            )

        return None
