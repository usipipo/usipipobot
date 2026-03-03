"""
Handlers for VPN server monitoring.

Author: uSipipo Team
Version: 1.0.0 - Server Monitoring
"""

from datetime import datetime, timezone
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.common.decorators import admin_required
from utils.logger import logger
from utils.spinner import SpinnerManager, admin_spinner_callback

from .keyboards_admin_vpn import AdminVpnKeyboards
from .messages_admin_vpn import AdminVpnMessages


class ServerMonitoringMixin:
    """Mixin for server monitoring operations."""

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
