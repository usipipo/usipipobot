"""
Handlers para gestión avanzada de llaves VPN de uSipipo.

Author: uSipipo Team
Version: 2.1.0 - Modernized Key Management
"""

import io

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from application.services.vpn_service import VpnService
from config import settings
from telegram_bot.common.base_handler import BaseHandler
from utils.logger import logger
from utils.telegram_utils import escape_markdown, format_percentage

from .keyboards_key_management import KeyManagementKeyboards
from .messages_key_management import KeyManagementMessages


class KeyManagementHandler(BaseHandler):
    """Handler para gestión avanzada de llaves VPN."""

    def __init__(self, vpn_service: VpnService):
        """
        Inicializa el handler de gestión de llaves.

        Args:
            vpn_service: Servicio de VPN
        """
        super().__init__(vpn_service, "VpnService")
        self.vpn_service = vpn_service
        logger.info("🔑 KeyManagementHandler inicializado")

    async def show_key_submenu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Muestra el menú principal de gestión de llaves.
        """
        query = update.callback_query

        if query is None:
            if update.effective_user is None:
                return
            user_id = update.effective_user.id
            if update.message is None:
                return
            try:
                user_status = await self.vpn_service.get_user_status(
                    user_id, current_user_id=user_id
                )
                keys = user_status.get("keys", [])

                keys_summary = {"total_count": len(keys)}

                for protocol in settings.get_vpn_protocols():
                    count = len(
                        [k for k in keys if k.key_type.lower() == protocol.lower()]
                    )
                    keys_summary[f"{protocol}_count"] = count

                if keys_summary["total_count"] == 0:
                    message = KeyManagementMessages.NO_KEYS
                else:
                    message = KeyManagementMessages.MAIN_MENU.format(
                        total_keys=escape_markdown(str(keys_summary["total_count"])),
                        outline_count=escape_markdown(str(keys_summary.get("outline_count", 0))),
                        wireguard_count=escape_markdown(str(keys_summary.get("wireguard_count", 0))),
                    )

                await update.message.reply_text(
                    text=message,
                    reply_markup=KeyManagementKeyboards.main_menu(keys_summary),
                    parse_mode="MarkdownV2",
                )

            except Exception as e:
                logger.error(f"Error mostrando submenú de llaves: {e}")
                if update.message is not None:
                    await update.message.reply_text(
                        text=KeyManagementMessages.Error.SYSTEM_ERROR,
                        parse_mode="MarkdownV2",
                    )
        else:
            await self._safe_answer_query(query)
            if update.effective_user is None:
                return
            user_id = update.effective_user.id

            try:
                user_status = await self.vpn_service.get_user_status(
                    user_id, current_user_id=user_id
                )
                keys = user_status.get("keys", [])

                keys_summary = {"total_count": len(keys)}

                for protocol in settings.get_vpn_protocols():
                    count = len(
                        [k for k in keys if k.key_type.lower() == protocol.lower()]
                    )
                    keys_summary[f"{protocol}_count"] = count

                if keys_summary["total_count"] == 0:
                    message = KeyManagementMessages.NO_KEYS
                else:
                    message = KeyManagementMessages.MAIN_MENU.format(
                        total_keys=escape_markdown(str(keys_summary["total_count"])),
                        outline_count=escape_markdown(str(keys_summary.get("outline_count", 0))),
                        wireguard_count=escape_markdown(str(keys_summary.get("wireguard_count", 0))),
                    )

                await self._safe_edit_message(
                    query,
                    context,
                    text=message,
                    reply_markup=KeyManagementKeyboards.main_menu(keys_summary),
                    parse_mode="MarkdownV2",
                )

            except Exception as e:
                logger.error(f"Error mostrando submenú de llaves: {e}")
                await self._safe_edit_message(
                    query,
                    context,
                    text=KeyManagementMessages.Error.SYSTEM_ERROR,
                    reply_markup=KeyManagementKeyboards.back_to_main(),
                    parse_mode="MarkdownV2",
                )

    async def show_keys_by_type(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Muestra llaves filtradas por tipo.
        """
        query = update.callback_query
        if query is None or query.data is None:
            return
        await self._safe_answer_query(query)

        # Extraer tipo del callback_data
        key_type = query.data.replace("keys_", "")
        if update.effective_user is None:
            return
        user_id = update.effective_user.id

        try:
            user_status = await self.vpn_service.get_user_status(
                user_id, current_user_id=user_id
            )
            all_keys = user_status.get("keys", [])

            # Filtrar llaves por tipo
            filtered_keys = [
                k for k in all_keys if k.key_type.lower() == key_type.lower()
            ]

            if not filtered_keys:
                message = KeyManagementMessages.NO_KEYS_TYPE.format(
                    type=escape_markdown(key_type.upper())
                )
                keyboard = KeyManagementKeyboards.back_to_submenu()
            else:
                message = KeyManagementMessages.KEYS_LIST_HEADER.format(
                    type=escape_markdown(key_type.upper())
                )
                keyboard = KeyManagementKeyboards.keys_list(filtered_keys)

                # Agregar información de cada llave
                for key in filtered_keys:
                    status = "🟢 Activa" if key.is_active else "🔴 Inactiva"
                    escaped_name = escape_markdown(key.name)
                    message += f"\n🔑 {escaped_name}\n   📊 {key.used_gb:.2f}/{key.data_limit_gb:.2f} GB\n   {status}\n"

            await self._safe_edit_message(
                query,
                context,
                text=message,
                reply_markup=keyboard,
                parse_mode="MarkdownV2",
            )

        except Exception as e:
            logger.error(f"Error mostrando llaves por tipo: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=KeyManagementMessages.Error.SYSTEM_ERROR,
                reply_markup=KeyManagementKeyboards.back_to_submenu(),
                parse_mode="MarkdownV2",
            )

    async def show_key_details(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Muestra detalles de una llave específica.
        """
        query = update.callback_query
        if query is None or query.data is None:
            return
        await self._safe_answer_query(query)

        # Extraer key_id del callback_data
        key_id = query.data.split("_")[-1]
        if update.effective_user is None:
            return
        user_id = update.effective_user.id

        try:
            key = await self.vpn_service.get_key_by_id(key_id, current_user_id=user_id)

            if not key or key.user_id != user_id:
                message = KeyManagementMessages.KEY_NOT_FOUND
                keyboard = KeyManagementKeyboards.back_to_submenu()
            else:
                status = "Activa" if key.is_active else "Inactiva"
                status_icon = "🟢" if key.is_active else "🔴"
                usage_percentage = (
                    (key.used_gb / key.data_limit_gb) * 100
                    if key.data_limit_gb > 0
                    else 0
                )

                usage_bar = format_percentage(key.used_gb, key.data_limit_gb)

                message = KeyManagementMessages.KEY_DETAILS.format(
                    name=escape_markdown(key.name),
                    type=escape_markdown(key.key_type.upper()),
                    server=escape_markdown(key.server or "N/A"),
                    usage_bar=usage_bar,  # No escapar - usa caracteres seguros
                    usage=escape_markdown(f"{key.used_gb:.1f}"),
                    limit=escape_markdown(f"{key.data_limit_gb:.1f}"),
                    percentage=escape_markdown(f"{usage_percentage:.0f}"),
                    status=escape_markdown(status),
                    status_icon=status_icon,
                    expires=escape_markdown(
                        key.expires_at.strftime("%d/%m/%Y") if key.expires_at else "N/A"
                    ),
                )

                keyboard = KeyManagementKeyboards.key_actions(
                    key_id, key.is_active, key.key_type
                )

            await self._safe_edit_message(
                query,
                context,
                text=message,
                reply_markup=keyboard,
                parse_mode="MarkdownV2",
            )

        except Exception as e:
            logger.error(f"Error mostrando detalles de llave: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=KeyManagementMessages.Error.SYSTEM_ERROR,
                reply_markup=KeyManagementKeyboards.back_to_submenu(),
                parse_mode="MarkdownV2",
            )

    def _generate_cyberpunk_progress_bar(self, percentage: float, width: int = 10) -> str:
        """Genera una barra de progreso estilo cyberpunk."""
        filled = int((percentage / 100) * width)
        empty = width - filled

        # Usar caracteres que no requieren escape en MarkdownV2
        # y tienen ancho consistente en fuentes monoespaciadas de Telegram
        filled_char = "█"
        empty_char = "░"

        return filled_char * filled + empty_char * empty

    async def show_key_statistics(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Muestra estadísticas detalladas de las llaves.
        """
        query = update.callback_query
        if query is None:
            return
        await self._safe_answer_query(query)

        if update.effective_user is None:
            return
        user_id = update.effective_user.id

        try:
            user_status = await self.vpn_service.get_user_status(
                user_id, current_user_id=user_id
            )
            keys = user_status.get("keys", [])

            if not keys:
                message = KeyManagementMessages.NO_KEYS_STATS
            else:
                total_keys = len(keys)
                active_keys = len([k for k in keys if k.is_active])
                total_usage = sum(k.used_gb for k in keys)
                total_limit = sum(k.data_limit_gb for k in keys)
                overall_percentage = (
                    (total_usage / total_limit * 100) if total_limit > 0 else 0
                )

                outline_keys = [k for k in keys if k.key_type.lower() == "outline"]
                wireguard_keys = [k for k in keys if k.key_type.lower() == "wireguard"]

                # Generar barra de progreso cyberpunk
                usage_bar = self._generate_cyberpunk_progress_bar(overall_percentage)

                message = KeyManagementMessages.STATISTICS.format(
                    total_keys=escape_markdown(str(total_keys)),
                    active_keys=escape_markdown(str(active_keys)),
                    total_usage=escape_markdown(f"{total_usage:.1f}"),
                    total_limit=escape_markdown(f"{total_limit:.1f}"),
                    percentage=escape_markdown(f"{overall_percentage:.0f}"),
                    usage_bar=usage_bar,  # No escapar - usa caracteres seguros
                    outline_count=escape_markdown(str(len(outline_keys))),
                    wireguard_count=escape_markdown(str(len(wireguard_keys))),
                    outline_usage=escape_markdown(f"{sum(k.used_gb for k in outline_keys):.1f}"),
                    wireguard_usage=escape_markdown(f"{sum(k.used_gb for k in wireguard_keys):.1f}"),
                )

            keyboard = KeyManagementKeyboards.back_to_submenu()

            await self._safe_edit_message(
                query,
                context,
                text=message,
                reply_markup=keyboard,
                parse_mode="MarkdownV2",
            )

        except Exception as e:
            logger.error(f"Error mostrando estadísticas: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=KeyManagementMessages.Error.SYSTEM_ERROR,
                reply_markup=KeyManagementKeyboards.back_to_submenu(),
                parse_mode="MarkdownV2",
            )

    async def handle_key_action(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Maneja acciones específicas sobre llaves (suspender, reactivar, eliminar, etc.).
        """
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

                elif action == "reactivate":
                    key.is_active = True
                    await self.vpn_service.update_key(key, current_user_id=user_id)
                    message = KeyManagementMessages.Actions.KEY_REACTIVATED

                elif action == "delete":
                    try:
                        await self.vpn_service.delete_key(
                            key_id, current_user_id=user_id
                        )
                        message = KeyManagementMessages.Actions.KEY_DELETED
                        keyboard = KeyManagementKeyboards.back_to_submenu()
                    except Exception as e:
                        if (
                            "Debes realizar al menos un depósito para eliminar claves"
                            in str(e)
                        ):
                            message = KeyManagementMessages.Error.DELETE_NOT_ALLOWED
                        else:
                            message = (
                                KeyManagementMessages.Error.OPERATION_FAILED.format(
                                    error=escape_markdown(str(e))
                                )
                            )
                        keyboard = KeyManagementKeyboards.back_to_submenu()

                elif action == "config":
                    await self.show_key_config(update, context)
                    return

                elif action == "stats":
                    await self.show_key_statistics(update, context)
                    return

                elif action == "rename":
                    # Iniciar flujo de renombrado
                    if context.user_data is not None:
                        context.user_data["rename_key_id"] = key_id
                    message = "✏️ Renombrar Llave\n\nPor favor, escribe el nuevo nombre para tu llave:"
                    keyboard = KeyManagementKeyboards.cancel_rename()
                    await self._safe_edit_message(
                        query,
                        context,
                        text=message,
                        reply_markup=keyboard,
                        parse_mode="MarkdownV2",
                    )
                    return

                else:
                    message = KeyManagementMessages.Error.INVALID_ACTION
                    keyboard = KeyManagementKeyboards.back_to_submenu()

            if keyboard is None and key is not None:
                keyboard = KeyManagementKeyboards.key_actions(
                    key_id, key.is_active, key.key_type
                )
            elif keyboard is None:
                keyboard = KeyManagementKeyboards.back_to_submenu()

            await self._safe_edit_message(
                query,
                context,
                text=message,
                reply_markup=keyboard,
                parse_mode="MarkdownV2",
            )

        except Exception as e:
            logger.error(f"Error en acción de llave {action}: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=KeyManagementMessages.Error.OPERATION_FAILED.format(error=escape_markdown(str(e))),
                reply_markup=KeyManagementKeyboards.back_to_submenu(),
                parse_mode="MarkdownV2",
            )

    async def show_key_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Muestra la configuración de una llave específica.
        """
        query = update.callback_query
        if query is None or query.data is None:
            return
        await self._safe_answer_query(query)

        key_id = query.data.split("_")[-1]
        if update.effective_user is None:
            return
        user_id = update.effective_user.id

        try:
            key = await self.vpn_service.get_key_by_id(key_id, current_user_id=user_id)

            if not key or key.user_id != user_id:
                message = KeyManagementMessages.KEY_NOT_FOUND
                keyboard = KeyManagementKeyboards.back_to_submenu()
            else:
                message = (
                    f"⚙️ **Configuración de {key.name}**\n\n"
                    f"📡 **Protocolo:** {key.key_type.upper()}\n"
                    f"🖥️ **Servidor:** {key.server or 'N/A'}\n"
                    f"📊 **Límite:** {key.data_limit_gb:.2f} GB\n"
                    f"🔄 **Reseteo:** {key.billing_reset_at.strftime('%d/%m/%Y')}\n\n"
                    "Selecciona una opción:"
                )
                keyboard = KeyManagementKeyboards.key_config(key_id)

            await self._safe_edit_message(
                query,
                context,
                text=message,
                reply_markup=keyboard,
                parse_mode="MarkdownV2",
            )

        except Exception as e:
            logger.error(f"Error mostrando configuración: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=KeyManagementMessages.Error.SYSTEM_ERROR,
                reply_markup=KeyManagementKeyboards.back_to_submenu(),
                parse_mode="MarkdownV2",
            )

    async def download_wireguard_config(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Envía el archivo .conf de una llave WireGuard al usuario.
        """
        query = update.callback_query
        if query is None or query.data is None:
            return
        await self._safe_answer_query(query)

        key_id = query.data.split("_")[-1]
        if update.effective_user is None:
            return
        user_id = update.effective_user.id

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
                caption=f"📄 Configuración WireGuard: *{key_name}*\n\nImporta este archivo en tu aplicación WireGuard.",
                parse_mode="MarkdownV2",
            )

        except Exception as e:
            logger.error(f"Error descargando config WireGuard: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=KeyManagementMessages.Error.SYSTEM_ERROR,
                reply_markup=KeyManagementKeyboards.back_to_submenu(),
                parse_mode="MarkdownV2",
            )

    async def get_outline_link(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Muestra el enlace de acceso ss:// para una llave Outline.
        """
        query = update.callback_query
        if query is None or query.data is None:
            return
        await self._safe_answer_query(query)

        key_id = query.data.split("_")[-1]
        if update.effective_user is None:
            return
        user_id = update.effective_user.id

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
                parse_mode="MarkdownV2",
            )

        except Exception as e:
            logger.error(f"Error obteniendo enlace Outline: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=KeyManagementMessages.Error.SYSTEM_ERROR,
                reply_markup=KeyManagementKeyboards.back_to_submenu(),
                parse_mode="MarkdownV2",
            )

    async def back_to_main_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Vuelve al menú principal."""
        query = update.callback_query
        if query is None:
            return
        await self._safe_answer_query(query)

        user = update.effective_user
        if user is None:
            return
        is_admin = user.id == int(settings.ADMIN_ID)

        from telegram_bot.common.keyboards import CommonKeyboards
        from telegram_bot.common.messages import CommonMessages

        await self._safe_edit_message(
            query,
            context,
            text=CommonMessages.Menu.WELCOME_BACK,
            reply_markup=CommonKeyboards.main_menu(is_admin=is_admin),
            parse_mode="MarkdownV2",
        )

    async def back_to_keys(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Vuelve al submenú de gestión de llaves."""
        await self.show_key_submenu(update, context)

    async def cancel_rename(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Cancela el proceso de renombrado.
        """
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
        """
        Procesa el mensaje de texto con el nuevo nombre para la llave.
        """
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
            # Limpiar estado
            del context.user_data["rename_key_id"]

            success = await self.vpn_service.rename_key(
                key_id, new_name, current_user_id=user_id
            )

            if success:
                message = KeyManagementMessages.Actions.KEY_RENAMED.format(
                    new_name=escape_markdown(new_name)
                )
            else:
                message = (
                    "❌ No se pudo renombrar la llave. Por favor, intenta de nuevo."
                )

            # Volver a los detalles de la llave
            await update.message.reply_text(
                text=message,
                reply_markup=KeyManagementKeyboards.back_to_submenu(),
                parse_mode="MarkdownV2",
            )

        except Exception as e:
            logger.error(f"Error procesando renombrado: {e}")
            if update.message is not None:
                await update.message.reply_text(
                    text=KeyManagementMessages.Error.SYSTEM_ERROR,
                    reply_markup=KeyManagementKeyboards.back_to_submenu(),
                    parse_mode="MarkdownV2",
                )


def get_key_management_handlers(vpn_service: VpnService):
    """Retorna los handlers de gestión de llaves."""
    handler = KeyManagementHandler(vpn_service)
    return [
        MessageHandler(filters.Regex("^🛡️ Mis Llaves$"), handler.show_key_submenu),
        CommandHandler("keys", handler.show_key_submenu),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handler.process_rename_key),
    ]


def get_key_management_callback_handlers(vpn_service: VpnService):
    """Retorna los handlers de callbacks para gestión de llaves."""
    handler = KeyManagementHandler(vpn_service)
    return [
        CallbackQueryHandler(handler.show_key_submenu, pattern="^key_management$"),
        CallbackQueryHandler(handler.back_to_main_menu, pattern="^main_menu$"),
        CallbackQueryHandler(handler.show_keys_by_type, pattern="^keys_"),
        CallbackQueryHandler(handler.show_key_details, pattern="^key_details_"),
        CallbackQueryHandler(handler.show_key_statistics, pattern="^key_stats$"),
        CallbackQueryHandler(handler.back_to_main_menu, pattern="^back_to_main$"),
        CallbackQueryHandler(handler.back_to_keys, pattern="^back_to_keys$"),
        CallbackQueryHandler(handler.handle_key_action, pattern="^key_suspend_"),
        CallbackQueryHandler(handler.handle_key_action, pattern="^key_reactivate_"),
        CallbackQueryHandler(handler.handle_key_action, pattern="^key_delete_"),
        CallbackQueryHandler(handler.handle_key_action, pattern="^key_config_"),
        CallbackQueryHandler(handler.show_key_config, pattern="^key_view_config_"),
        CallbackQueryHandler(handler.handle_key_action, pattern="^key_rename_"),
        CallbackQueryHandler(handler.handle_key_action, pattern="^key_qr_"),
        CallbackQueryHandler(handler.handle_key_action, pattern="^key_change_server_"),
        CallbackQueryHandler(handler.handle_key_action, pattern="^key_extend_"),
        CallbackQueryHandler(
            handler.download_wireguard_config, pattern="^key_download_wg_"
        ),
        CallbackQueryHandler(handler.get_outline_link, pattern="^key_get_link_"),
        CallbackQueryHandler(handler.cancel_rename, pattern="^cancel_rename$"),
    ]
