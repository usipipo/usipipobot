"""
Handlers para visualización de llaves VPN.

Author: uSipipo Team
Version: 1.0.0 - Refactor from handlers_key_management.py
"""

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.features.key_management.messages_key_management import KeyManagementMessages
from telegram_bot.features.key_management.keyboards_key_management import KeyManagementKeyboards
from utils.logger import logger
from utils.telegram_utils import escape_markdown, format_percentage


class ViewKeysMixin:
    """Mixin para visualización de llaves VPN."""

    async def show_keys_by_type(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra llaves filtradas por tipo."""
        query = update.callback_query
        if query is None or query.data is None:
            return
        await self._safe_answer_query(query)

        # Extraer tipo del callback_data
        key_type = query.data.replace("keys_", "")
        if update.effective_user is None:
            return
        user_id = update.effective_user.id
        logger.info(f"User {user_id} viewing keys by type: {key_type}")

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
                    message += (
                        f"\n🔑 {escaped_name}\n"
                        f"   📊 {key.used_gb:.2f}/{key.data_limit_gb:.2f} GB\n"
                        f"   {status}\n"
                    )

            await self._safe_edit_message(
                query,
                context,
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error mostrando llaves por tipo: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=KeyManagementMessages.Error.SYSTEM_ERROR,
                reply_markup=KeyManagementKeyboards.back_to_submenu(),
                parse_mode="Markdown",
            )

    async def show_key_details(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra detalles de una llave específica."""
        query = update.callback_query
        if query is None or query.data is None:
            return
        await self._safe_answer_query(query)

        # Extraer key_id del callback_data
        key_id = query.data.split("_")[-1]
        if update.effective_user is None:
            return
        user_id = update.effective_user.id
        logger.info(f"User {user_id} viewing details for key {key_id}")

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
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error mostrando detalles de llave: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=KeyManagementMessages.Error.SYSTEM_ERROR,
                reply_markup=KeyManagementKeyboards.back_to_submenu(),
                parse_mode="Markdown",
            )

    def _generate_cyberpunk_progress_bar(
        self, percentage: float, width: int = 10
    ) -> str:
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
        """Muestra estadísticas detalladas de las llaves."""
        query = update.callback_query
        if query is None:
            return
        await self._safe_answer_query(query)

        if update.effective_user is None:
            return
        user_id = update.effective_user.id
        logger.info(f"User {user_id} viewing key statistics")

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
                    outline_usage=escape_markdown(
                        f"{sum(k.used_gb for k in outline_keys):.1f}"
                    ),
                    wireguard_usage=escape_markdown(
                        f"{sum(k.used_gb for k in wireguard_keys):.1f}"
                    ),
                )

            keyboard = KeyManagementKeyboards.back_to_submenu()

            await self._safe_edit_message(
                query,
                context,
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error mostrando estadísticas: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=KeyManagementMessages.Error.SYSTEM_ERROR,
                reply_markup=KeyManagementKeyboards.back_to_submenu(),
                parse_mode="Markdown",
            )
