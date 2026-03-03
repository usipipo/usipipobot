"""
Handlers para renombrado de llaves VPN.

Author: uSipipo Team
Version: 1.0.0 - Refactor from handlers_key_management.py
"""

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.features.key_management.messages_key_management import KeyManagementMessages
from telegram_bot.features.key_management.keyboards_key_management import KeyManagementKeyboards
from utils.logger import logger
from utils.telegram_utils import escape_markdown


class RenameKeyMixin:
    """Mixin para renombrado de llaves VPN."""

    async def cancel_rename(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancela el proceso de renombrado."""
        query = update.callback_query
        if query is None:
            return
        await self._safe_answer_query(query)

        if context.user_data is not None and "rename_key_id" in context.user_data:
            del context.user_data["rename_key_id"]

        await self.show_key_submenu(update, context)

    async def process_rename_key(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Procesa el mensaje de texto con el nuevo nombre para la llave."""
        if context.user_data is None:
            return
        key_id = context.user_data.get("rename_key_id")
        if not key_id:
            return

        if update.message is None or update.message.text is None:
            return
        new_name = update.message.text.strip()
        if update.effective_user is None:
            return
        user_id = update.effective_user.id

        try:
            logger.info(
                f"User {user_id} attempting to rename key {key_id} to '{new_name}'"
            )
            # Limpiar estado
            del context.user_data["rename_key_id"]

            success = await self.vpn_service.rename_key(
                key_id, new_name, current_user_id=user_id
            )

            if success:
                message = KeyManagementMessages.Actions.KEY_RENAMED.format(
                    new_name=escape_markdown(new_name)
                )
                logger.info(f"User {user_id} renamed key {key_id} to '{new_name}'")
            else:
                message = (
                    "❌ No se pudo renombrar la llave. Por favor, intenta de nuevo."
                )

            # Volver a los detalles de la llave
            await update.message.reply_text(
                text=message,
                reply_markup=KeyManagementKeyboards.back_to_submenu(),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error procesando renombrado: {e}")
            if update.message is not None:
                await update.message.reply_text(
                    text=KeyManagementMessages.Error.SYSTEM_ERROR,
                    reply_markup=KeyManagementKeyboards.back_to_submenu(),
                    parse_mode="Markdown",
                )
