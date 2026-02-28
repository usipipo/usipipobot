"""
Handlers for admin VPN management.

Author: uSipipo Team
Version: 1.0.0 - VPN Server Management
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from telegram import Update
from telegram.ext import ContextTypes

from application.services.vpn_infrastructure_service import VpnInfrastructureService
from telegram_bot.common.base_handler import BaseHandler
from telegram_bot.common.decorators import admin_required
from utils.logger import logger
from utils.spinner import SpinnerManager, admin_spinner_callback

from .keyboards_admin_vpn import AdminVpnKeyboards
from .messages_admin_vpn import AdminVpnMessages

KEYS_PER_PAGE = 10


class AdminVpnHandler(BaseHandler):
    """Handler for VPN server management."""

    def __init__(self, vpn_service: VpnInfrastructureService):
        super().__init__()
        self.vpn_service = vpn_service
        logger.info("⚡ AdminVpnHandler inicializado")

    def _get_handlers(self) -> List[tuple]:
        """Define handler callbacks."""
        return [
            ("admin_vpn", self.show_vpn_menu),
            ("vpn_status", self.show_server_status),
            ("vpn_manage_wireguard", self.manage_server),
            ("vpn_manage_outline", self.manage_server),
            ("vpn_server_status_wireguard", self.show_server_details),
            ("vpn_server_status_outline", self.show_server_details),
            ("vpn_list_keys_wireguard", self.list_server_keys),
            ("vpn_list_keys_outline", self.list_server_keys),
            ("vpn_cleanup_ghosts", self.cleanup_ghost_keys),
            ("vpn_key_details_wireguard_", self.show_key_details),
            ("vpn_key_details_outline_", self.show_key_details),
            ("vpn_key_enable_wireguard_", self.handle_key_enable),
            ("vpn_key_enable_outline_", self.handle_key_enable),
            ("vpn_key_disable_wireguard_", self.handle_key_disable),
            ("vpn_key_disable_outline_", self.handle_key_disable),
            ("vpn_key_delete_wireguard_", self.confirm_delete_key),
            ("vpn_key_delete_outline_", self.confirm_delete_key),
            ("vpn_confirm_delete_wireguard_", self.execute_delete_key),
            ("vpn_confirm_delete_outline_", self.execute_delete_key),
            ("vpn_cancel_delete_wireguard_", self.cancel_key_action),
            ("vpn_cancel_delete_outline_", self.cancel_key_action),
            ("vpn_keys_page_wireguard_", self.keys_page),
            ("vpn_keys_page_outline_", self.keys_page),
        ]

    @admin_required
    async def show_vpn_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main VPN management menu."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query:
            await self._safe_edit_message(
                query,
                context,
                text=AdminVpnMessages.MAIN_MENU,
                reply_markup=AdminVpnKeyboards.vpn_management_menu(),
                parse_mode="Markdown",
            )
        else:
            await self._reply_message(
                update,
                text=AdminVpnMessages.MAIN_MENU,
                reply_markup=AdminVpnKeyboards.vpn_management_menu(),
                parse_mode="Markdown",
                context=context,
            )
        return None

    @admin_required
    @admin_spinner_callback
    async def show_server_status(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: Optional[int] = None,
    ):
        """Show WireGuard + Outline server status."""
        query = update.callback_query
        await self._safe_answer_query(query)

        try:
            wg_metrics = await self.vpn_service.get_server_metrics("wireguard")
            ol_metrics = await self.vpn_service.get_server_metrics("outline")

            wg_health = "✅ Saludable" if wg_metrics.get("is_healthy") else "❌ No disponible"
            ol_health = "✅ Saludable" if ol_metrics.get("is_healthy") else "❌ No disponible"

            message = AdminVpnMessages.SERVER_STATUS.format(
                wg_health=wg_health,
                wg_total=wg_metrics.get("total_keys", 0),
                wg_active=wg_metrics.get("active_keys", 0),
                ol_health=ol_health,
                ol_name=ol_metrics.get("server_name", "N/A"),
                ol_total=ol_metrics.get("total_keys", 0),
                ol_active=ol_metrics.get("active_keys", 0),
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            )

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminVpnKeyboards.back_to_vpn_menu(),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error showing server status: {e}")
            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=AdminVpnMessages.ERROR_OPERATION_FAILED.format(error=str(e)),
                reply_markup=AdminVpnKeyboards.back_to_vpn_menu(),
                parse_mode="Markdown",
            )

        return None

    @admin_required
    async def manage_server(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show server-specific actions."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return None

        server_type = query.data.replace("vpn_manage_", "")

        message = AdminVpnMessages.SERVER_MANAGE_HEADER.format(
            server_type=server_type.upper()
        )

        await self._safe_edit_message(
            query,
            context,
            text=message,
            reply_markup=AdminVpnKeyboards.server_actions(server_type),
            parse_mode="Markdown",
        )
        return None

    @admin_required
    @admin_spinner_callback
    async def show_server_details(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: Optional[int] = None,
    ):
        """Show detailed status for a specific server."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return None

        server_type = query.data.replace("vpn_server_status_", "")

        try:
            metrics = await self.vpn_service.get_server_metrics(server_type)

            health = "✅ Saludable" if metrics.get("is_healthy") else "❌ No disponible"

            message = (
                f"📊 **Estado de {server_type.upper()}**\n\n"
                f"🟢 **Estado:** {health}\n"
                f"🔑 **Total claves:** {metrics.get('total_keys', 0)}\n"
                f"✅ **Claves activas:** {metrics.get('active_keys', 0)}\n"
            )

            if server_type == "outline":
                message += f"🏷️ **Nombre servidor:** {metrics.get('server_name', 'N/A')}\n"

            if metrics.get("error"):
                message += f"\n⚠️ **Error:** {metrics.get('error')}"

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminVpnKeyboards.back_to_server(server_type),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error showing server details: {e}")
            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=AdminVpnMessages.ERROR_OPERATION_FAILED.format(error=str(e)),
                reply_markup=AdminVpnKeyboards.back_to_vpn_menu(),
                parse_mode="Markdown",
            )

        return None

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
            keys = await self.vpn_service.list_server_keys(server_type)

            if not keys:
                await SpinnerManager.replace_spinner_with_message(
                    update,
                    context,
                    spinner_message_id,
                    text=AdminVpnMessages.NO_KEYS.format(server_type=server_type.upper()),
                    reply_markup=AdminVpnKeyboards.back_to_server(server_type),
                    parse_mode="Markdown",
                )
                return None

            page = 1
            total_pages = max(1, (len(keys) + KEYS_PER_PAGE - 1) // KEYS_PER_PAGE)
            offset = (page - 1) * KEYS_PER_PAGE
            page_keys = keys[offset : offset + KEYS_PER_PAGE]

            message = AdminVpnMessages.KEYS_LIST_HEADER.format(
                server_type=server_type.upper()
            ) + f"📊 Total: {len(keys)} claves\n\n"

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
            keys = await self.vpn_service.list_server_keys(server_type)

            if not keys:
                await self._safe_edit_message(
                    query,
                    context,
                    text=AdminVpnMessages.NO_KEYS.format(server_type=server_type.upper()),
                    reply_markup=AdminVpnKeyboards.back_to_server(server_type),
                    parse_mode="Markdown",
                )
                return None

            total_pages = max(1, (len(keys) + KEYS_PER_PAGE - 1) // KEYS_PER_PAGE)
            offset = (page - 1) * KEYS_PER_PAGE
            page_keys = keys[offset : offset + KEYS_PER_PAGE]

            message = AdminVpnMessages.KEYS_LIST_HEADER.format(
                server_type=server_type.upper()
            ) + f"📊 Total: {len(keys)} claves\n\n"

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
        key_id = parts[-1]

        try:
            keys = await self.vpn_service.list_server_keys(key_type)
            key = next((k for k in keys if k.get("id") == key_id), None)

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

            message = AdminVpnMessages.KEY_DETAILS.format(
                key_id=key_id[:8],
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
                    key_id, key.get("is_active", False), key_type
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
        key_id = parts[-1]

        try:
            result = await self.vpn_service.enable_key(key_id, key_type)

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
        key_id = parts[-1]

        try:
            result = await self.vpn_service.disable_key(key_id, key_type)

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
        key_id = parts[-1]

        message = AdminVpnMessages.CONFIRM_DELETE_KEY.format(key_id=key_id[:8])

        await self._safe_edit_message(
            query,
            context,
            text=message,
            reply_markup=AdminVpnKeyboards.confirmation("delete", key_id, key_type),
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
        key_id = parts[-1]

        try:
            result = await self.vpn_service.delete_key_complete(key_id, key_type)

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

    @admin_required
    @admin_spinner_callback
    async def cleanup_ghost_keys(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: Optional[int] = None,
    ):
        """Run ghost key cleanup."""
        query = update.callback_query
        await self._safe_answer_query(query)

        try:
            result = await self.vpn_service.cleanup_ghost_keys(days_inactive=90)

            if result.get("ghosts_found", 0) == 0:
                message = AdminVpnMessages.NO_GHOST_KEYS
            else:
                errors_section = ""
                if result.get("errors"):
                    errors_section = AdminVpnMessages.CLEANUP_ERRORS.format(
                        errors="\n".join(f"• {e}" for e in result.get("errors", []))
                    )

                message = AdminVpnMessages.CLEANUP_REPORT.format(
                    total_checked=result.get("total_checked", 0),
                    ghosts_found=result.get("ghosts_found", 0),
                    disabled_count=result.get("disabled_count", 0),
                    errors_section=errors_section,
                )

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminVpnKeyboards.back_to_vpn_menu(),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error cleaning up ghost keys: {e}")
            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=AdminVpnMessages.ERROR_OPERATION_FAILED.format(error=str(e)),
                reply_markup=AdminVpnKeyboards.back_to_vpn_menu(),
                parse_mode="Markdown",
            )

        return None


def get_admin_vpn_handlers(vpn_service: VpnInfrastructureService) -> List[Any]:
    """Get all admin VPN handlers."""
    handler = AdminVpnHandler(vpn_service)
    return handler.get_handlers()
