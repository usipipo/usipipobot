"""
Mixin para acciones de usuario (registro y referidos).

Author: uSipipo Team
Version: 3.0.0 - Refactored into mixins
"""

from telegram import Update
from telegram.ext import ContextTypes

from utils.logger import logger
from utils.spinner import registration_spinner


class UserActionsMixin:
    """Mixin para acciones de usuario como registro y referidos."""

    @registration_spinner
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja el comando /start y el registro de usuarios.

        Acepta parametro start con codigo de referido:
        /start REFERRAL_CODE
        """
        if not update.effective_user:
            return
        if not update.message:
            return

        user = update.effective_user
        logger.info(f"start_handler iniciado para usuario {user.id}")

        try:
            existing_user = await self.vpn_service.user_repo.get_by_id(user.id, user.id)

            if not existing_user:
                full_name = user.first_name or ""
                if user.last_name:
                    full_name = f"{full_name} {user.last_name}".strip()

                await self.vpn_service.user_repo.create_user(
                    user_id=user.id, username=user.username, full_name=full_name
                )
                welcome_message = self.messages.Welcome.NEW_USER_SIMPLIFIED

                if context.args and len(context.args) > 0:
                    referral_code = context.args[0]
                    await self._process_referral(user.id, referral_code)

                logger.info(f"Nuevo usuario registrado: {user.id} - {user.first_name}")
            else:
                welcome_message = self.messages.Welcome.RETURNING_USER_SIMPLIFIED
                logger.info(f"Usuario existente: {user.id} - {user.first_name}")

            miniapp_url = self._get_miniapp_url()

            from telegram_bot.keyboards import MainMenuKeyboard

            await update.message.reply_text(
                text=welcome_message,
                reply_markup=MainMenuKeyboard.main_menu_with_admin(
                    admin_id=int(self.settings.ADMIN_ID),
                    current_user_id=user.id,
                    miniapp_url=miniapp_url,
                ),
                parse_mode="Markdown",
            )

        except (AttributeError, ValueError) as e:
            logger.error(f"Error en start_handler para usuario {user.id}: {e}")
            from telegram_bot.keyboards import MainMenuKeyboard

            await update.message.reply_text(
                text=self.messages.Error.REGISTRATION_FAILED,
                reply_markup=MainMenuKeyboard.main_menu(miniapp_url=self._get_miniapp_url()),
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
                    f"Referido procesado: usuario {new_user_id} " f"con codigo {referral_code}"
                )
            else:
                logger.warning(
                    f"Referido no procesado para {new_user_id}: " f"{result.get('error')}"
                )

        except Exception as e:
            logger.error(f"Error procesando referido: {e}")
