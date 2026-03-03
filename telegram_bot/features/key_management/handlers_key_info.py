"""
Handlers para información de llaves VPN (configs, links).

Author: uSipipo Team
Version: 1.0.0 - Refactor from handlers_key_management.py
"""

import io

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.features.key_management.messages_key_management import KeyManagementMessages
from telegram_bot.features.key_management.keyboards_key_management import KeyManagementKeyboards
from utils.logger import logger


class KeyInfoMixin:
    """Mixin para información de llaves VPN (descarga de configs, enlaces)."""

    async def download_wireguard_config(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Envía el archivo .conf de una llave WireGuard al usuario."""
        query = update.callback_query
        if query is None or query.data is None:
            return
        await self._safe_answer_query(query)

        key_id = query.data.split("_")[-1]
        if update.effective_user is None:
            return
        user_id = update.effective_user.id
        logger.info(f"User {user_id} downloading WireGuard config for key {key_id}")

        try:
            config_data = await self.vpn_service.get_wireguard_config(
                key_id, current_user_id=user_id
            )
            config_str = config_data.get("config_string")
            key_name = config_data.get("external_id", "wg_config")

            if not config_str or "no disponible" in config_str.lower():
                await self._safe_edit_message(
                    query,
                    context,
                    text="❌ La configuración no está disponible en este momento.",
                    reply_markup=KeyManagementKeyboards.back_to_submenu(),
                )
                return

            bio = io.BytesIO(config_str.encode("utf-8"))
            bio.name = f"{key_name}.conf"

            if update.effective_chat is None:
                return
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=bio,
                filename=f"{key_name}.conf",
                caption=(
                    f"📄 Configuración WireGuard: *{key_name}*\n\n"
                    "Importa este archivo en tu aplicación WireGuard."
                ),
                parse_mode="Markdown",
            )
            logger.info(
                f"User {user_id} successfully downloaded WireGuard config for key {key_id}"
            )

        except Exception as e:
            logger.error(f"Error descargando config WireGuard: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=KeyManagementMessages.Error.SYSTEM_ERROR,
                reply_markup=KeyManagementKeyboards.back_to_submenu(),
                parse_mode="Markdown",
            )

    async def get_outline_link(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra el enlace de acceso ss:// para una llave Outline."""
        query = update.callback_query
        if query is None or query.data is None:
            return
        await self._safe_answer_query(query)

        key_id = query.data.split("_")[-1]
        if update.effective_user is None:
            return
        user_id = update.effective_user.id
        logger.info(f"User {user_id} getting Outline link for key {key_id}")

        try:
            config_data = await self.vpn_service.get_outline_config(
                key_id, current_user_id=user_id
            )
            access_url = config_data.get("access_url")

            if not access_url or "no disponible" in access_url.lower():
                await self._safe_edit_message(
                    query,
                    context,
                    text="❌ El enlace no está disponible en este momento.",
                    reply_markup=KeyManagementKeyboards.back_to_submenu(),
                )
                return

            message = (
                f"🔗 **Tu Clave de Acceso Outline**\n\n"
                f"Copia el siguiente código y pégalo en tu aplicación Outline:\n\n"
                f"`{access_url}`"
            )

            await self._safe_edit_message(
                query,
                context,
                text=message,
                reply_markup=KeyManagementKeyboards.back_to_submenu(),
                parse_mode="Markdown",
            )
            logger.info(
                f"User {user_id} successfully retrieved Outline link for key {key_id}"
            )

        except Exception as e:
            logger.error(f"Error obteniendo enlace Outline: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=KeyManagementMessages.Error.SYSTEM_ERROR,
                reply_markup=KeyManagementKeyboards.back_to_submenu(),
                parse_mode="Markdown",
            )
