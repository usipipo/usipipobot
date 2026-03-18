"""
Handlers for server latency monitoring.

Provides /latency command and callback handlers for viewing server metrics.
"""

from datetime import datetime, timezone
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from infrastructure.cache.redis_client import get_redis_client
from infrastructure.cache.stats_cache import ServerStats, get_latest_stats, save_stats
from infrastructure.metrics import collect_server_stats
from utils.logger import logger

from .keyboards_key_management import KeyManagementKeyboards
from .messages_key_management import LatencyMessages


class LatencyMixin:
    """Mixin for server latency monitoring operations."""

    async def show_server_latency(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        """Show server latency and metrics."""
        query = update.callback_query
        if query is None:
            return

        await query.answer()
        logger.info(f"User {update.effective_user.id} viewing server latency")

        try:
            redis_client = get_redis_client()

            # Try to get cached stats
            stats = await get_latest_stats(redis_client)

            if not stats:
                # No stats available - collect now
                await query.edit_message_text(
                    text=LatencyMessages.COLLECTING,
                    reply_markup=KeyManagementKeyboards.back_to_keys(),
                    parse_mode="Markdown",
                )

                # Collect fresh stats
                stats = await collect_server_stats()
                await save_stats(stats, redis_client)

            # Format message
            message = self._format_latency_message(stats)

            keyboard = KeyManagementKeyboards.latency_actions()

            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

            await redis_client.close()

        except Exception as e:
            logger.error(f"Error showing server latency: {e}")
            await query.edit_message_text(
                text="❌ *Error al obtener latencia*\n\n" "🔄 Intenta nuevamente",
                reply_markup=KeyManagementKeyboards.back_to_keys(),
                parse_mode="Markdown",
            )

    async def refresh_server_latency(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        """Refresh server latency metrics."""
        query = update.callback_query
        if query is None:
            return

        await query.answer("🔄 Actualizando...")
        logger.info(f"User {update.effective_user.id} refreshing server latency")

        try:
            redis_client = get_redis_client()

            # Collect fresh stats
            stats = await collect_server_stats()
            await save_stats(stats, redis_client)

            # Format message
            message = self._format_latency_message(stats)

            keyboard = KeyManagementKeyboards.latency_actions()

            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

            await redis_client.close()

        except Exception as e:
            logger.error(f"Error refreshing server latency: {e}")
            await query.answer("❌ Error al actualizar", show_alert=True)

    def _format_latency_message(self, stats) -> str:
        """Format latency stats into message."""
        icon, label = stats.status_label

        # Format protocols line
        outline_icon = "✅" if stats.outline_status else "❌"
        wg_icon = "✅" if stats.wireguard_status else "❌"
        dns_line = ""
        if stats.dnsproxy_status:
            dns_line = " · 🛡️ AdBlock ACTIVO"

        protocols = LatencyMessages.PROTOCOLS_SECTION.format(
            outline_icon=outline_icon,
            wg_icon=wg_icon,
            wg_active=stats.active_wg_connections,
            dns_line=dns_line,
        )

        # Calculate age of stats
        stats_time = datetime.fromisoformat(stats.timestamp.replace("Z", "+00:00"))
        age_seconds = int((datetime.now(timezone.utc) - stats_time).total_seconds())

        message = LatencyMessages.SERVER_STATUS.format(
            status_icon=icon,
            status_label=label,
            ping_ms=stats.ping_ms,
            cpu_percent=stats.cpu_percent,
            ram_percent=stats.ram_percent,
            ram_used_mb=stats.ram_used_mb,
            ram_total_mb=stats.ram_total_mb,
            protocols=protocols,
            uptime_hours=stats.uptime_hours,
            age_seconds=age_seconds,
        )

        return message

    async def latency_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        """Handle /latency command."""
        if update.effective_user is None:
            return

        user_id = update.effective_user.id
        logger.info(f"User {user_id} executed /latency command")

        try:
            redis_client = get_redis_client()

            # Try to get cached stats
            stats = await get_latest_stats(redis_client)

            if not stats:
                # Collect fresh stats
                stats = await collect_server_stats()
                await save_stats(stats, redis_client)

            # Format message
            message = self._format_latency_message(stats)

            keyboard = KeyManagementKeyboards.latency_actions()

            if update.message:
                await update.message.reply_text(
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )

            await redis_client.close()

        except Exception as e:
            logger.error(f"Error in /latency command: {e}")
            if update.message:
                await update.message.reply_text(
                    text="❌ *Error al obtener latencia*\n\n" "🔄 Intenta nuevamente",
                    parse_mode="Markdown",
                )
