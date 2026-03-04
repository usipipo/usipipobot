"""
Mixin para perfil de usuario (estado, info, historial).

Author: uSipipo Team
Version: 3.0.0 - Refactored into mixins
"""

from datetime import datetime, timezone
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from application.services.admin_service import AdminService
from utils.logger import logger


class UserProfileMixin:
    """Mixin para operaciones de perfil de usuario."""

    async def status_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        admin_service: Optional[AdminService] = None,
    ):
        """
        Muestra el estado del usuario o panel administrativo.
        """
        if not update.effective_user:
            return

        telegram_id = update.effective_user.id
        user_name = update.effective_user.username or update.effective_user.first_name

        try:
            is_admin = str(telegram_id) == str(self.settings.ADMIN_ID)

            if is_admin and admin_service:
                stats = await admin_service.get_dashboard_stats(
                    current_user_id=telegram_id
                )
                text = self._format_admin_dashboard(user_name, stats)
            else:
                status_data = await self.vpn_service.get_user_status(
                    telegram_id, telegram_id
                )
                user_entity = status_data.get("user")

                join_date = "N/A"
                if (
                    user_entity
                    and hasattr(user_entity, "created_at")
                    and user_entity.created_at
                ):
                    join_date = user_entity.created_at.strftime("%Y-%m-%d")

                status_text = "Inactivo ⚠️"
                if user_entity and (
                    getattr(user_entity, "is_active", False)
                    or getattr(user_entity, "status", None) == "active"
                ):
                    status_text = "Activo ✅"

                text = (
                    self.messages.Status.HEADER
                    + "\n\n"
                    + self.messages.Status.USER_INFO.format(
                        name=user_name,
                        user_id=telegram_id,
                        join_date=join_date,
                        status=status_text,
                    )
                )

            is_admin_menu = telegram_id == int(self.settings.ADMIN_ID)
            await self._reply_message(
                update,
                text=text,
                reply_markup=self.keyboards.main_menu(is_admin=is_admin_menu),
                parse_mode="Markdown",
                context=context,
            )

        except (AttributeError, ValueError, KeyError) as e:
            logger.error(f"❌ Error en status_handler para usuario {telegram_id}: {e}")
            await self._reply_message(
                update,
                text=self.messages.Error.STATUS_FAILED,
                reply_markup=self.keyboards.main_menu(),
                parse_mode="Markdown",
                context=context,
            )

    async def info_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Muestra información detallada del usuario.
        """
        if not update.effective_user:
            return

        telegram_id = update.effective_user.id

        try:
            if self.user_profile_service:
                profile = await self.user_profile_service.get_user_profile_summary(
                    telegram_id, telegram_id
                )

                if not profile:
                    await self._reply_message(
                        update,
                        text=self.messages.Error.INFO_FAILED,
                        reply_markup=self.keyboards.main_menu(),
                        parse_mode="Markdown",
                        context=context,
                    )
                    return

                join_date = profile.created_at.strftime("%Y-%m-%d")
                days_since_join = (datetime.now(timezone.utc) - profile.created_at).days
                status_text = "Activo" if profile.status == "active" else "Inactivo"

                total_gb = profile.total_used_gb + profile.free_data_remaining_gb
                data_percentage = (
                    (profile.total_used_gb / total_gb * 100) if total_gb > 0 else 0
                )

                text = (
                    self.messages.Info.HEADER
                    + self.messages.Info.USER_INFO(
                        name=profile.full_name or "N/A",
                        user_id=profile.user_id,
                        username=profile.username or "N/A",
                        join_date=join_date,
                        days_since_join=days_since_join,
                        status=status_text,
                        data_used=f"{profile.total_used_gb:.2f} GB",
                        data_total=f"{total_gb:.2f} GB",
                        data_percentage=data_percentage,
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
                status_data = await self.vpn_service.get_user_status(
                    telegram_id, telegram_id
                )
                user_entity = status_data.get("user")

                if not user_entity:
                    await self._reply_message(
                        update,
                        text=self.messages.Error.INFO_FAILED,
                        reply_markup=self.keyboards.main_menu(),
                        parse_mode="Markdown",
                        context=context,
                    )
                    return

                join_date = "N/A"
                days_since_join = 0
                if hasattr(user_entity, "created_at") and user_entity.created_at:
                    join_date = user_entity.created_at.strftime("%Y-%m-%d")
                    days_since_join = (
                        datetime.now(timezone.utc) - user_entity.created_at
                    ).days

                status_text = "Inactivo"
                if (
                    getattr(user_entity, "is_active", False)
                    or getattr(user_entity, "status", None) == "active"
                ):
                    status_text = "Activo"

                keys = status_data.get("keys", [])
                keys_used = len([k for k in keys if getattr(k, "is_active", True)])
                data_used_gb = status_data.get("total_used_gb", 0)

                text = (
                    self.messages.Info.HEADER
                    + self.messages.Info.USER_INFO(
                        name=user_entity.full_name or "N/A",
                        user_id=telegram_id,
                        username=user_entity.username or "N/A",
                        join_date=join_date,
                        days_since_join=days_since_join,
                        status=status_text,
                        data_used=f"{data_used_gb:.2f} GB",
                        data_total="10.00 GB",
                        data_percentage=data_used_gb / 10 * 100 if data_used_gb else 0,
                        free_data_remaining="10.00 GB",
                        active_packages=0,
                        keys_used=keys_used,
                        keys_total=user_entity.max_keys,
                        referral_code="N/A",
                        total_referrals=0,
                        credits=user_entity.referral_credits or 0,
                    )
                )

            is_admin_menu = telegram_id == int(self.settings.ADMIN_ID)
            await self._reply_message(
                update,
                text=text,
                reply_markup=self.keyboards.main_menu(is_admin=is_admin_menu),
                parse_mode="Markdown",
                context=context,
            )

        except (AttributeError, ValueError, KeyError) as e:
            logger.error(f"❌ Error en info_handler para usuario {telegram_id}: {e}")
            await self._reply_message(
                update,
                text=self.messages.Error.INFO_FAILED,
                reply_markup=self.keyboards.main_menu(),
                parse_mode="Markdown",
                context=context,
            )

    async def history_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Muestra el historial de transacciones del usuario.
        """
        if not update.effective_user:
            return

        telegram_id = update.effective_user.id

        try:
            if not self.user_profile_service:
                await self._reply_message(
                    update,
                    text="❌ Servicio de historial no disponible.",
                    reply_markup=self.keyboards.main_menu(),
                    parse_mode="Markdown",
                    context=context,
                )
                return

            transactions = await self.user_profile_service.get_user_transactions(
                telegram_id, limit=5
            )

            if not transactions:
                await self._reply_message(
                    update,
                    text=self.messages.History.NO_TRANSACTIONS,
                    reply_markup=self.keyboards.main_menu(),
                    parse_mode="Markdown",
                    context=context,
                )
                return

            text = self.messages.History.HEADER
            for i, tx in enumerate(transactions, 1):
                date_str = tx.get("created_at", "N/A")
                if hasattr(date_str, "strftime"):
                    date_str = date_str.strftime("%Y-%m-%d")
                description = tx.get("description", tx.get("type", "Transacción"))
                amount = tx.get("amount", 0)
                status = tx.get("status", "completado")

                text += self.messages.History.TRANSACTION_ITEM.format(
                    number=i,
                    date=date_str,
                    description=description,
                    amount=f"{amount} ⭐" if amount else "N/A",
                    status=status,
                )
                text += "\n"

            text += self.messages.History.FOOTER

            is_admin_menu = telegram_id == int(self.settings.ADMIN_ID)
            await self._reply_message(
                update,
                text=text,
                reply_markup=self.keyboards.main_menu(is_admin=is_admin_menu),
                parse_mode="Markdown",
                context=context,
            )

        except (AttributeError, ValueError, KeyError) as e:
            logger.error(f"❌ Error en history_handler para usuario {telegram_id}: {e}")
            await self._reply_message(
                update,
                text="❌ Error al obtener historial.",
                reply_markup=self.keyboards.main_menu(),
                parse_mode="Markdown",
                context=context,
            )

    def _format_admin_dashboard(self, user_name: str, stats: dict) -> str:
        """
        Formatea el panel de control administrativo.
        """
        return self.messages.Status.ADMIN_DASHBOARD.format(
            name=user_name,
            total_users=stats.get("total_users", 0),
            active_users=stats.get("active_users", 0),
            total_keys=stats.get("total_keys", 0),
            active_keys=stats.get("active_keys", 0),
            server_load=stats.get("server_load", "N/A"),
        )
