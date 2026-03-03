"""
Handlers for VPN ghost key cleanup operations.

Author: uSipipo Team
Version: 1.0.0 - Cleanup Operations
"""

from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.common.decorators import admin_required
from utils.logger import logger
from utils.spinner import SpinnerManager, admin_spinner_callback

from .keyboards_admin_vpn import AdminVpnKeyboards
from .messages_admin_vpn import AdminVpnMessages


class CleanupMixin:
    """Mixin for ghost key cleanup operations."""

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
