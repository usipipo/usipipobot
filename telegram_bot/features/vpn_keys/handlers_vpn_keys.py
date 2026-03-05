"""
Handlers para gestión de llaves VPN de uSipipo.

Author: uSipipo Team
Version: 2.0.0 - Feature-based architecture
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from application.services.vpn_service import VpnService
from config import settings
from telegram_bot.common.keyboards import CommonKeyboards
from utils.logger import logger
from utils.qr_generator import QrGenerator
from utils.spinner import vpn_spinner
from utils.telegram_utils import escape_markdown

from .keyboards_vpn_keys import VpnKeysKeyboards
from .messages_vpn_keys import VpnKeysMessages

if TYPE_CHECKING:
    from domain.entities.user import User

# Estados de la conversación
SELECT_TYPE, INPUT_NAME = range(2)


class VpnKeysHandler:
    """Handler para gestión de llaves VPN."""

    def __init__(self, vpn_service: VpnService):
        """
        Inicializa el handler de llaves VPN.

        Args:
            vpn_service: Servicio de VPN
        """
        self.vpn_service = vpn_service
        logger.info("🔑 VpnKeysHandler inicializado")

    async def start_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia el flujo de creación preguntando el tipo de VPN."""
        if not update.effective_user:
            return ConversationHandler.END
        telegram_id = update.effective_user.id
        is_admin = telegram_id == int(settings.ADMIN_ID)

        logger.info(f"🔑 User {telegram_id} started key creation flow")

        user = await self._get_or_create_user(telegram_id)
        can_create, message = await self.vpn_service.can_user_create_key(
            user, current_user_id=telegram_id
        )

        if not can_create:
            logger.warning(
                f"⚠️ User {telegram_id} reached key limit ({user.max_keys} keys)"
            )
            # Obtener cantidad de claves usadas para mostrar en el mensaje
            keys = await self.vpn_service.get_user_keys(telegram_id, telegram_id)
            used_keys = len([k for k in keys if k.is_active])
            error_message = VpnKeysMessages.Error.KEY_LIMIT_REACHED.format(
                used_keys=used_keys, max_keys=user.max_keys
            )
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(
                    text=error_message,
                    reply_markup=VpnKeysKeyboards.limit_reached_menu(is_admin=is_admin),
                    parse_mode="Markdown",
                )
            elif update.message:
                await update.message.reply_text(
                    text=error_message,
                    reply_markup=VpnKeysKeyboards.limit_reached_menu(is_admin=is_admin),
                    parse_mode="Markdown",
                )
            return ConversationHandler.END

        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text=VpnKeysMessages.SELECT_TYPE,
                reply_markup=VpnKeysKeyboards.vpn_types(),
                parse_mode="Markdown",
            )
        elif update.message:
            await update.message.reply_text(
                text=VpnKeysMessages.SELECT_TYPE,
                reply_markup=VpnKeysKeyboards.vpn_types(),
                parse_mode="Markdown",
            )
        return SELECT_TYPE

    async def _get_or_create_user(self, telegram_id: int) -> "User":
        """Helper para obtener o crear usuario."""
        from domain.entities.user import User

        user = await self.vpn_service.user_repo.get_by_id(telegram_id, telegram_id)
        if not user:
            user = User(telegram_id=telegram_id)
        return user

    async def type_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja la selección del protocolo y pide el nombre de la llave."""
        query = update.callback_query
        if not query or not query.data:
            return ConversationHandler.END
        await query.answer()

        key_type = "outline" if "outline" in query.data else "wireguard"
        if context.user_data is not None:
            context.user_data["tmp_key_type"] = key_type

        user_id = update.effective_user.id if update.effective_user else None
        logger.info(f"🔑 User {user_id} selected key type: {key_type}")

        cancel_keyboard = VpnKeysKeyboards.cancel_creation()

        escaped_key_type = escape_markdown(key_type.upper())
        await query.edit_message_text(
            text=f"🛡️ Has seleccionado *{escaped_key_type}*.\n\nEscribe un nombre para identificar tu nueva llave (ej: Mi Laptop):",
            parse_mode="Markdown",
            reply_markup=cancel_keyboard,
        )
        return INPUT_NAME

    @vpn_spinner
    async def name_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Finaliza la creación, genera archivos/QR y entrega al usuario."""
        if not update.effective_user or not update.message or not update.message.text:
            return ConversationHandler.END
        key_name = update.message.text
        tmp_key_type = (
            context.user_data.get("tmp_key_type") if context.user_data else None
        )
        if not tmp_key_type:
            return ConversationHandler.END
        key_type: str = tmp_key_type
        telegram_id = update.effective_user.id

        logger.info(f"🔑 User {telegram_id} named key: {key_name} (type: {key_type})")

        try:
            new_key = await self.vpn_service.create_key(
                telegram_id, key_type, key_name, current_user_id=telegram_id
            )

            logger.info(
                f"✅ Key {new_key.id} created successfully for user {telegram_id}"
            )

            safe_name = "".join(x for x in key_name if x.isalnum())
            file_id = f"{telegram_id}_{safe_name}"

            is_admin = telegram_id == int(settings.ADMIN_ID)

            qr_path = QrGenerator.generate_vpn_qr(new_key.key_data, file_id)

            if key_type == "outline":
                escaped_name = escape_markdown(key_name)
                escaped_data = escape_markdown(new_key.key_data)

                caption = (
                    VpnKeysMessages.Success.KEY_CREATED_WITH_DATA.format(
                        type="OUTLINE",
                        name=escaped_name,
                        data_limit=new_key.data_limit_gb,
                    )
                    + f"\n\nCopia el siguiente código en tu aplicación Outline:\n```\n{escaped_data}\n```"
                )

                with open(qr_path, "rb") as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=caption,
                        parse_mode="Markdown",
                        reply_markup=CommonKeyboards.main_menu(is_admin=is_admin),
                    )

            elif key_type == "wireguard":
                conf_path = QrGenerator.save_conf_file(new_key.key_data, file_id)

                escaped_name = escape_markdown(key_name)
                caption = (
                    VpnKeysMessages.Success.KEY_CREATED_WITH_DATA.format(
                        type="WIREGUARD",
                        name=escaped_name,
                        data_limit=new_key.data_limit_gb,
                    )
                    + "\n\nEscanea el QR en tu móvil o usa el archivo adjunto en tu PC."
                )

                with open(qr_path, "rb") as photo:
                    await update.message.reply_photo(
                        photo=photo, caption=caption, parse_mode="Markdown"
                    )

                with open(conf_path, "rb") as document:
                    await update.message.reply_document(
                        document=document,
                        filename=f"{key_name}.conf",
                        caption="📁 *Configuración WireGuard*\n\n🔑 Tu nueva llave VPN está lista para usar\n\n⚠️ *Guarda este archivo en un lugar seguro*",
                        parse_mode="Markdown",
                        reply_markup=CommonKeyboards.main_menu(is_admin=is_admin),
                    )

            logger.info(f"✅ Llave {key_type} creada para usuario {telegram_id}")

        except Exception as e:
            logger.error(f"❌ Error en creación de llave: {e}")
            is_admin = telegram_id == int(settings.ADMIN_ID)
            await update.message.reply_text(
                text=VpnKeysMessages.Error.CREATION_FAILED.format(error=str(e)),
                reply_markup=CommonKeyboards.main_menu(is_admin=is_admin),
            )

        return ConversationHandler.END

    async def cancel_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancela la conversación desde comando /cancel."""
        if not update.effective_user or not update.message:
            return ConversationHandler.END
        telegram_id = update.effective_user.id
        is_admin = telegram_id == int(settings.ADMIN_ID)

        logger.info(f"🔑 User {telegram_id} cancelled key creation")

        await update.message.reply_text(
            text=VpnKeysMessages.CANCELLED,
            reply_markup=CommonKeyboards.main_menu(is_admin=is_admin),
        )
        return ConversationHandler.END

    async def cancel_creation_from_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Cancela la conversación desde botón de cancelar."""
        query = update.callback_query
        if not query:
            return ConversationHandler.END
        await query.answer()

        if context.user_data is not None:
            context.user_data.pop("tmp_key_type", None)

        if not update.effective_user:
            return ConversationHandler.END
        telegram_id = update.effective_user.id
        is_admin = telegram_id == int(settings.ADMIN_ID)

        await query.edit_message_text(
            text=VpnKeysMessages.CANCELLED + "\n\nHas vuelto al menú principal",
            reply_markup=CommonKeyboards.main_menu(is_admin=is_admin),
        )
        return ConversationHandler.END


def get_vpn_keys_handler(vpn_service: VpnService) -> ConversationHandler:
    """
    Configuración del ConversationHandler para creación de llaves VPN.

    Args:
        vpn_service: Servicio de VPN

    Returns:
        ConversationHandler: Handler configurado
    """
    handler = VpnKeysHandler(vpn_service)

    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^➕ Crear Nueva$"), handler.start_creation),
            CallbackQueryHandler(handler.start_creation, pattern="^create_key$"),
            CommandHandler("newkey", handler.start_creation),
        ],
        states={
            SELECT_TYPE: [
                CallbackQueryHandler(handler.type_selected, pattern="^type_"),
                CallbackQueryHandler(
                    handler.cancel_creation_from_callback, pattern="^cancel_create_key$"
                ),
            ],
            INPUT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handler.name_received),
                CallbackQueryHandler(
                    handler.cancel_creation_from_callback, pattern="^cancel_create_key$"
                ),
            ],
        },
        fallbacks=[CommandHandler("cancel", handler.cancel_creation)],
        per_message=False,
        per_chat=True,
        per_user=True,
        allow_reentry=True,
    )


def get_vpn_keys_handlers(vpn_service: VpnService):
    """
    Retorna los handlers de gestión de llaves VPN.

    Args:
        vpn_service: Servicio de VPN

    Returns:
        list: Lista de handlers
    """
    return [
        get_vpn_keys_handler(vpn_service),
    ]


def get_vpn_keys_callback_handlers(vpn_service: VpnService):
    """
    Retorna los handlers de callbacks para VPN Keys.

    Args:
        vpn_service: Servicio de VPN

    Returns:
        list: Lista de CallbackQueryHandler

    Note:
        El callback 'create_key' ya está manejado por el ConversationHandler
        en get_vpn_keys_handler(), por lo que no se duplica aquí.
    """
    return []
