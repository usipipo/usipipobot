"""
Handlers para acciones sobre llaves VPN (suspender, reactivar).

Author: uSipipo Team
Version: 1.0.0 - Refactor from handlers_key_management.py
"""

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.features.key_management.keyboards_key_management import KeyManagementKeyboards
from telegram_bot.features.key_management.messages_key_management import KeyManagementMessages
from utils.logger import logger
from utils.telegram_utils import escape_markdown


class KeyActionsMixin:
    """Mixin para acciones sobre llaves VPN (suspender, reactivar)."""

    async def handle_key_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja acciones específicas sobre llaves (suspender, reactivar, etc.)."""
        query = update.callback_query
        if query is None or query.data is None:
            return
        await self._safe_answer_query(query)

        parts = query.data.split("_")
        action = parts[1] if len(parts) > 1 else ""
        key_id = parts[2] if len(parts) > 2 else ""
        if update.effective_user is None:
            return
        user_id = update.effective_user.id
        keyboard = None

        # Log action at appropriate level
        if action in ["suspend", "delete"]:
            logger.warning(f"User {user_id} performing action {action} on key {key_id}")
        else:
            logger.info(f"User {user_id} performing action {action} on key {key_id}")

        try:
            key = await self.vpn_service.get_key_by_id(key_id, current_user_id=user_id)

            if not key or key.user_id != user_id:
                message = KeyManagementMessages.KEY_NOT_FOUND
                keyboard = KeyManagementKeyboards.back_to_submenu()
            else:
                if action == "suspend":
                    key.is_active = False
                    await self.vpn_service.update_key(key, current_user_id=user_id)
                    message = KeyManagementMessages.Actions.KEY_SUSPENDED
                    logger.info(f"User {user_id} successfully suspended key {key_id}")

                elif action == "reactivate":
                    key.is_active = True
                    await self.vpn_service.update_key(key, current_user_id=user_id)
                    message = KeyManagementMessages.Actions.KEY_REACTIVATED
                    logger.info(f"User {user_id} successfully reactivated key {key_id}")

                elif action == "rename":
                    # Iniciar flujo de renombrado
                    if context.user_data is not None:
                        context.user_data["rename_key_id"] = key_id
                    message = (
                        "✏️ Renombrar Llave\n\n" "Por favor, escribe el nuevo nombre para tu llave:"
                    )
                    keyboard = KeyManagementKeyboards.cancel_rename()
                    await self._safe_edit_message(
                        query,
                        context,
                        text=message,
                        reply_markup=keyboard,
                        parse_mode="Markdown",
                    )
                    return

                else:
                    message = KeyManagementMessages.Error.INVALID_ACTION
                    keyboard = KeyManagementKeyboards.back_to_submenu()

            if keyboard is None and key is not None:
                keyboard = KeyManagementKeyboards.key_actions(key_id, key.is_active, key.key_type)
            elif keyboard is None:
                keyboard = KeyManagementKeyboards.back_to_submenu()

            await self._safe_edit_message(
                query,
                context,
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error en acción de llave {action}: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=KeyManagementMessages.Error.OPERATION_FAILED.format(
                    error=escape_markdown(str(e))
                ),
                reply_markup=KeyManagementKeyboards.back_to_submenu(),
                parse_mode="Markdown",
            )
