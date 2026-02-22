"""
Handlers para gestión de usuarios de uSipipo.

Author: uSipipo Team
Version: 2.0.0 - Feature-based architecture
"""

from typing import Optional

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from application.services.admin_service import AdminService

# Local imports
from application.services.vpn_service import VpnService

# First party imports
from config import settings
from telegram_bot.keyboards import MainMenuKeyboard
from utils.logger import logger
from utils.spinner import registration_spinner

from .keyboards_user_management import UserManagementKeyboards
from .messages_user_management import UserManagementMessages


class UserManagementHandler:
    """Handler para gestión de usuarios."""

    def __init__(self, vpn_service: VpnService):
        """
        Inicializa el handler de gestión de usuarios.

        Args:
            vpn_service: Servicio de VPN
        """
        self.vpn_service = vpn_service
        logger.info("👤 UserManagementHandler inicializado")

    @registration_spinner
    async def start_handler(self, update: Update, _context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja el comando /start y el registro de usuarios.
        """
        logger.info(
            f"🔄 start_handler iniciado para usuario {update.effective_user.id}"
        )

        user = update.effective_user

        try:
            # Verificar si el usuario ya existe
            existing_user = await self.vpn_service.user_repo.get_by_id(user.id, user.id)

            if not existing_user:
                # Construir full_name
                full_name = user.first_name or ""
                if user.last_name:
                    full_name = f"{full_name} {user.last_name}".strip()

                # Crear nuevo usuario
                await self.vpn_service.user_repo.create_user(
                    user_id=user.id, username=user.username, full_name=full_name
                )
                welcome_message = UserManagementMessages.Welcome.NEW_USER_SIMPLIFIED

                logger.info(
                    f"✅ Nuevo usuario registrado: {user.id} - {user.first_name}"
                )
            else:
                welcome_message = (
                    UserManagementMessages.Welcome.RETURNING_USER_SIMPLIFIED
                )
                logger.info(f"👋 Usuario existente: {user.id} - {user.first_name}")

            # Determinar si es admin
            is_admin = user.id == int(settings.ADMIN_ID)

            await update.message.reply_text(
                text=welcome_message,
                reply_markup=MainMenuKeyboard.main_menu_with_admin(
                    admin_id=int(settings.ADMIN_ID), current_user_id=user.id
                ),
                parse_mode="Markdown",
            )

        except (AttributeError, ValueError) as e:
            logger.error(f"❌ Error en start_handler para usuario {user.id}: {e}")
            await update.message.reply_text(
                text=UserManagementMessages.Error.REGISTRATION_FAILED,
                reply_markup=MainMenuKeyboard.main_menu(),
            )

    async def main_menu_callback(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Maneja los callbacks del menú principal.
        """
        query = update.callback_query
        await query.answer()

        callback_data = query.data
        user_id = update.effective_user.id

        if callback_data == "show_keys":
            from telegram_bot.features.key_management.handlers_key_management import (
                KeyManagementHandler,
            )

            handler = KeyManagementHandler(self.vpn_service)
            await handler.show_key_submenu(update, _context)

        elif callback_data == "create_key":
            from telegram_bot.features.vpn_keys.handlers_vpn_keys import VpnKeysHandler

            handler = VpnKeysHandler(self.vpn_service)
            await handler.start_creation(update, _context)

        elif callback_data == "buy_data":
            from application.services.common.container import get_container
            from application.services.payment_service import PaymentService
            from telegram_bot.features.payments.handlers_payments import PaymentsHandler

            container = get_container()
            payment_service = container.resolve(PaymentService)
            handler = PaymentsHandler(payment_service, self.vpn_service)
            await handler.show_payment_menu(update, _context)

        elif callback_data == "show_usage":
            from telegram_bot.features.user_management.handlers_user_management import (
                UserManagementHandler,
            )

            await self.status_handler(update, _context)

        elif callback_data == "help":
            await query.edit_message_text(
                text=UserManagementMessages.Welcome.HELP_TEXT,
                reply_markup=MainMenuKeyboard.main_menu(),
            )

        elif callback_data == "admin_panel":
            from application.services.common.container import get_container
            from telegram_bot.features.admin.handlers_admin import AdminHandler

            container = get_container()
            admin_service = container.resolve(AdminService)
            handler = AdminHandler(admin_service)
            await handler.admin_menu(update, _context)

    async def status_handler(
        self,
        update: Update,
        _context: ContextTypes.DEFAULT_TYPE,
        admin_service: Optional[AdminService] = None,
    ):
        """
        Muestra el estado del usuario o panel administrativo.
        """
        telegram_id = update.effective_user.id
        user_name = update.effective_user.username or update.effective_user.first_name

        try:
            # Validar si es admin
            is_admin = str(telegram_id) == str(settings.ADMIN_ID)

            if is_admin and admin_service:
                # Mostrar panel de control administrativo
                stats = await admin_service.get_dashboard_stats()
                text = self._format_admin_dashboard(user_name, stats)
            else:
                # Mostrar estado de usuario regular
                status_data = await self.vpn_service.get_user_status(telegram_id)
                user_entity = status_data.get("user")

                # Formatear fecha de unión
                join_date = "N/A"
                if (
                    user_entity
                    and hasattr(user_entity, "created_at")
                    and user_entity.created_at
                ):
                    join_date = user_entity.created_at.strftime("%Y-%m-%d")

                # Determinar estado
                status_text = "Inactivo ⚠️"
                if user_entity and (
                    getattr(user_entity, "is_active", False)
                    or getattr(user_entity, "status", None) == "active"
                ):
                    status_text = "Activo ✅"

                text = (
                    UserManagementMessages.Status.HEADER
                    + "\n\n"
                    + UserManagementMessages.Status.USER_INFO.format(
                        name=user_name,
                        user_id=telegram_id,
                        join_date=join_date,
                        status=status_text,
                    )
                )

            # Determinar si es admin para el menú
            is_admin_menu = telegram_id == int(settings.ADMIN_ID)

            # Verificar si hay mensaje para responder
            if update.message:
                await update.message.reply_text(
                    text=text,
                    reply_markup=UserManagementKeyboards.main_menu(
                        is_admin=is_admin_menu
                    ),
                    parse_mode="Markdown",
                )
            elif update.callback_query:
                await update.callback_query.message.edit_text(
                    text=text,
                    reply_markup=UserManagementKeyboards.main_menu(
                        is_admin=is_admin_menu
                    ),
                    parse_mode="Markdown",
                )

        except (AttributeError, ValueError, KeyError) as e:
            logger.error(f"❌ Error en status_handler para usuario {telegram_id}: {e}")
            # Verificar si hay mensaje para responder
            if update.message:
                await update.message.reply_text(
                    text=UserManagementMessages.Error.STATUS_FAILED,
                    reply_markup=UserManagementKeyboards.main_menu(),
                )
            elif update.callback_query:
                await update.callback_query.message.edit_text(
                    text=UserManagementMessages.Error.STATUS_FAILED,
                    reply_markup=UserManagementKeyboards.main_menu(),
                )

    async def info_handler(self, update: Update, _context: ContextTypes.DEFAULT_TYPE):
        """
        Muestra información detallada del usuario.
        """
        telegram_id = update.effective_user.id
        user_name = update.effective_user.username or update.effective_user.first_name
        full_name = update.effective_user.first_name or ""
        if update.effective_user.last_name:
            full_name = f"{full_name} {update.effective_user.last_name}".strip()

        try:
            # Obtener datos completos del usuario
            status_data = await self.vpn_service.get_user_status(telegram_id)
            user_entity = status_data.get("user")

            if not user_entity:
                await update.message.reply_text(
                    text=UserManagementMessages.Error.INFO_FAILED,
                    reply_markup=UserManagementKeyboards.main_menu(),
                )
                return

            # Formatear fecha de unión
            join_date = "N/A"
            if hasattr(user_entity, "created_at") and user_entity.created_at:
                join_date = user_entity.created_at.strftime("%Y-%m-%d")

            # Determinar estado
            status_text = "Inactivo ⚠️"
            if (
                getattr(user_entity, "is_active", False)
                or getattr(user_entity, "status", None) == "active"
            ):
                status_text = "Activo ✅"

            # Obtener información adicional del usuario y claves
            keys = status_data.get("keys", [])
            keys_used = len([k for k in keys if getattr(k, "is_active", True)])
            keys_total = user_entity.max_keys
            data_used = f"{status_data.get('total_used_gb', 0):.2f} GB"
            balance = user_entity.balance_stars

            # Determinar plan
            plan = "VIP" if user_entity.is_vip_active() else "Gratis"

            # Valores por defecto para nivel y logros
            level = 1
            achievements = 0

            # Construir mensaje de información
            text = (
                UserManagementMessages.Info.HEADER
                + "\n\n"
                + UserManagementMessages.Info.USER_INFO.format(
                    name=full_name,
                    user_id=telegram_id,
                    username=update.effective_user.username or "N/A",
                    join_date=join_date,
                    status=status_text,
                    plan=plan,
                    keys_used=keys_used,
                    keys_total=keys_total,
                    data_used=data_used,
                    balance=balance,
                    level=level,
                    achievements=achievements,
                )
            )

            # Determinar si es admin para el menú
            is_admin_menu = telegram_id == int(settings.ADMIN_ID)

            await update.message.reply_text(
                text=text,
                reply_markup=UserManagementKeyboards.main_menu(is_admin=is_admin_menu),
                parse_mode="Markdown",
            )

        except (AttributeError, ValueError, KeyError) as e:
            logger.error(f"❌ Error en info_handler para usuario {telegram_id}: {e}")
            await update.message.reply_text(
                text=UserManagementMessages.Error.INFO_FAILED,
                reply_markup=UserManagementKeyboards.main_menu(),
            )

    def _format_admin_dashboard(self, user_name: str, stats: dict) -> str:
        """
        Formatea el panel de control administrativo.
        """
        return UserManagementMessages.Status.ADMIN_DASHBOARD.format(
            name=user_name,
            total_users=stats.get("total_users", 0),
            active_users=stats.get("active_users", 0),
            total_keys=stats.get("total_keys", 0),
            active_keys=stats.get("active_keys", 0),
            server_load=stats.get("server_load", "N/A"),
        )


def get_user_management_handlers(vpn_service: VpnService):
    """
    Retorna los handlers de gestión de usuarios.

    Args:
        vpn_service: Servicio de VPN

    Returns:
        list: Lista de handlers
    """
    handler = UserManagementHandler(vpn_service)

    return [
        CommandHandler("start", handler.start_handler),
        CommandHandler("info", handler.info_handler),
        MessageHandler(filters.Regex("^📊 Estado$"), handler.status_handler),
        CommandHandler("status", handler.status_handler),
    ]


def get_user_callback_handlers(vpn_service: VpnService):
    """
    Retorna los handlers de callbacks para gestión de usuarios.

    Args:
        vpn_service: Servicio de VPN

    Returns:
        list: Lista de CallbackQueryHandler
    """
    handler = UserManagementHandler(vpn_service)

    return [
        CallbackQueryHandler(
            lambda u, c: handler.status_handler(u, c, None), pattern="^status$"
        ),
        CallbackQueryHandler(
            handler.main_menu_callback,
            pattern="^(show_keys|create_key|buy_data|show_usage|help|admin_panel)$",
        ),
    ]
