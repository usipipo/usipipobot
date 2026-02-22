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
from application.services.user_profile_service import UserProfileService

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

    def __init__(
        self,
        vpn_service: VpnService,
        user_profile_service: Optional[UserProfileService] = None,
    ):
        """
        Inicializa el handler de gestión de usuarios.

        Args:
            vpn_service: Servicio de VPN
            user_profile_service: Servicio de perfil de usuario (opcional)
        """
        self.vpn_service = vpn_service
        self.user_profile_service = user_profile_service
        logger.info("👤 UserManagementHandler inicializado")

    @registration_spinner
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja el comando /start y el registro de usuarios.
        
        Acepta parametro start con codigo de referido:
        /start REFERRAL_CODE
        """
        logger.info(
            f"start_handler iniciado para usuario {update.effective_user.id}"
        )

        user = update.effective_user

        try:
            existing_user = await self.vpn_service.user_repo.get_by_id(user.id, user.id)

            if not existing_user:
                full_name = user.first_name or ""
                if user.last_name:
                    full_name = f"{full_name} {user.last_name}".strip()

                await self.vpn_service.user_repo.create_user(
                    user_id=user.id, username=user.username, full_name=full_name
                )
                welcome_message = UserManagementMessages.Welcome.NEW_USER_SIMPLIFIED

                if context.args and len(context.args) > 0:
                    referral_code = context.args[0]
                    await self._process_referral(user.id, referral_code)

                logger.info(
                    f"Nuevo usuario registrado: {user.id} - {user.first_name}"
                )
            else:
                welcome_message = (
                    UserManagementMessages.Welcome.RETURNING_USER_SIMPLIFIED
                )
                logger.info(f"Usuario existente: {user.id} - {user.first_name}")

            is_admin = user.id == int(settings.ADMIN_ID)

            await update.message.reply_text(
                text=welcome_message,
                reply_markup=MainMenuKeyboard.main_menu_with_admin(
                    admin_id=int(settings.ADMIN_ID), current_user_id=user.id
                ),
                parse_mode="Markdown",
            )

        except (AttributeError, ValueError) as e:
            logger.error(f"Error en start_handler para usuario {user.id}: {e}")
            await update.message.reply_text(
                text=UserManagementMessages.Error.REGISTRATION_FAILED,
                reply_markup=MainMenuKeyboard.main_menu(),
            )

    async def _process_referral(self, new_user_id: int, referral_code: str):
        """
        Procesa el codigo de referido para un nuevo usuario.
        
        Args:
            new_user_id: ID del nuevo usuario
            referral_code: Codigo de referido
        """
        try:
            from application.services.common.container import get_container
            from application.services.referral_service import ReferralService

            container = get_container()
            referral_service = container.resolve(ReferralService)

            result = await referral_service.register_referral(
                new_user_id=new_user_id,
                referral_code=referral_code,
                current_user_id=new_user_id,
            )

            if result.get("success"):
                logger.info(
                    f"Referido procesado: usuario {new_user_id} con codigo {referral_code}"
                )
            else:
                logger.warning(
                    f"Referido no procesado para {new_user_id}: {result.get('error')}"
                )

        except Exception as e:
            logger.error(f"Error procesando referido: {e}")

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

        elif callback_data == "show_history":
            await self.history_handler(update, _context)

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

        try:
            if self.user_profile_service:
                profile = await self.user_profile_service.get_user_profile_summary(
                    telegram_id, telegram_id
                )

                if not profile:
                    message = update.message or update.callback_query.message
                    await message.reply_text(
                        text=UserManagementMessages.Error.INFO_FAILED,
                        reply_markup=UserManagementKeyboards.main_menu(),
                    )
                    return

                join_date = profile.created_at.strftime("%Y-%m-%d")
                status_text = "Activo ✅" if profile.status == "active" else "Inactivo ⚠️"

                text = (
                    UserManagementMessages.Info.HEADER
                    + "\n\n"
                    + UserManagementMessages.Info.USER_INFO.format(
                        name=profile.full_name or "N/A",
                        user_id=profile.user_id,
                        username=profile.username or "N/A",
                        join_date=join_date,
                        status=status_text,
                        data_used=f"{profile.total_used_gb:.2f} GB",
                        free_data_remaining=f"{profile.free_data_remaining_gb:.2f} GB",
                        active_packages=profile.active_packages,
                        keys_used=profile.keys_used,
                        keys_total=profile.max_keys,
                        referral_code=profile.referral_code or "N/A",
                        total_referrals=profile.total_referrals,
                        credits=profile.referral_credits,
                    )
                )
            else:
                status_data = await self.vpn_service.get_user_status(telegram_id)
                user_entity = status_data.get("user")

                if not user_entity:
                    message = update.message or update.callback_query.message
                    await message.reply_text(
                        text=UserManagementMessages.Error.INFO_FAILED,
                        reply_markup=UserManagementKeyboards.main_menu(),
                    )
                    return

                join_date = "N/A"
                if hasattr(user_entity, "created_at") and user_entity.created_at:
                    join_date = user_entity.created_at.strftime("%Y-%m-%d")

                status_text = "Inactivo ⚠️"
                if getattr(user_entity, "is_active", False) or getattr(
                    user_entity, "status", None
                ) == "active":
                    status_text = "Activo ✅"

                keys = status_data.get("keys", [])
                keys_used = len([k for k in keys if getattr(k, "is_active", True)])
                data_used = f"{status_data.get('total_used_gb', 0):.2f} GB"

                text = (
                    UserManagementMessages.Info.HEADER
                    + "\n\n"
                    + UserManagementMessages.Info.USER_INFO.format(
                        name=user_entity.full_name or "N/A",
                        user_id=telegram_id,
                        username=user_entity.username or "N/A",
                        join_date=join_date,
                        status=status_text,
                        data_used=data_used,
                        free_data_remaining="N/A",
                        active_packages=0,
                        keys_used=keys_used,
                        keys_total=user_entity.max_keys,
                        referral_code="N/A",
                        total_referrals=0,
                        credits=user_entity.referral_credits or 0,
                    )
                )

            is_admin_menu = telegram_id == int(settings.ADMIN_ID)
            message = update.message or update.callback_query.message

            await message.reply_text(
                text=text,
                reply_markup=UserManagementKeyboards.main_menu(is_admin=is_admin_menu),
                parse_mode="Markdown",
            )

        except (AttributeError, ValueError, KeyError) as e:
            logger.error(f"❌ Error en info_handler para usuario {telegram_id}: {e}")
            message = update.message or update.callback_query.message
            await message.reply_text(
                text=UserManagementMessages.Error.INFO_FAILED,
                reply_markup=UserManagementKeyboards.main_menu(),
            )

    async def history_handler(self, update: Update, _context: ContextTypes.DEFAULT_TYPE):
        """
        Muestra el historial de transacciones del usuario.
        """
        telegram_id = update.effective_user.id

        try:
            if not self.user_profile_service:
                message = update.message or update.callback_query.message
                await message.reply_text(
                    text="❌ Servicio de historial no disponible.",
                    reply_markup=UserManagementKeyboards.main_menu(),
                )
                return

            transactions = await self.user_profile_service.get_user_transactions(
                telegram_id, limit=5
            )

            message = update.message or update.callback_query.message

            if not transactions:
                await message.reply_text(
                    text=UserManagementMessages.History.NO_TRANSACTIONS,
                    reply_markup=UserManagementKeyboards.main_menu(),
                    parse_mode="Markdown",
                )
                return

            text = UserManagementMessages.History.HEADER
            for i, tx in enumerate(transactions, 1):
                date_str = tx.get("created_at", "N/A")
                if hasattr(date_str, "strftime"):
                    date_str = date_str.strftime("%Y-%m-%d")
                description = tx.get("description", tx.get("type", "Transacción"))
                amount = tx.get("amount", 0)
                status = tx.get("status", "completado")

                text += UserManagementMessages.History.TRANSACTION_ITEM.format(
                    number=i,
                    date=date_str,
                    description=description,
                    amount=f"{amount} ⭐" if amount else "N/A",
                    status=status,
                )
                text += "\n"

            text += UserManagementMessages.History.FOOTER

            is_admin_menu = telegram_id == int(settings.ADMIN_ID)
            await message.reply_text(
                text=text,
                reply_markup=UserManagementKeyboards.main_menu(is_admin=is_admin_menu),
                parse_mode="Markdown",
            )

        except (AttributeError, ValueError, KeyError) as e:
            logger.error(
                f"❌ Error en history_handler para usuario {telegram_id}: {e}"
            )
            message = update.message or update.callback_query.message
            await message.reply_text(
                text="❌ Error al obtener historial.",
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


def get_user_management_handlers(
    vpn_service: VpnService,
    user_profile_service: Optional[UserProfileService] = None,
):
    """
    Retorna los handlers de gestión de usuarios.

    Args:
        vpn_service: Servicio de VPN
        user_profile_service: Servicio de perfil de usuario (opcional)

    Returns:
        list: Lista de handlers
    """
    handler = UserManagementHandler(vpn_service, user_profile_service)

    return [
        CommandHandler("start", handler.start_handler),
        CommandHandler("info", handler.info_handler),
        CommandHandler("history", handler.history_handler),
        MessageHandler(filters.Regex("^📊 Estado$"), handler.status_handler),
        CommandHandler("status", handler.status_handler),
    ]


def get_user_callback_handlers(
    vpn_service: VpnService,
    user_profile_service: Optional[UserProfileService] = None,
):
    """
    Retorna los handlers de callbacks para gestión de usuarios.

    Args:
        vpn_service: Servicio de VPN
        user_profile_service: Servicio de perfil de usuario (opcional)

    Returns:
        list: Lista de CallbackQueryHandler
    """
    handler = UserManagementHandler(vpn_service, user_profile_service)

    return [
        CallbackQueryHandler(
            lambda u, c: handler.status_handler(u, c, None), pattern="^status$"
        ),
        CallbackQueryHandler(
            handler.main_menu_callback,
            pattern="^(show_keys|create_key|buy_data|show_usage|help|admin_panel|show_history)$",
        ),
    ]
