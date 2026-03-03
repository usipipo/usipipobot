"""
Servicio de estadísticas administrativas para el bot uSipipo.

Author: uSipipo Team
Version: 1.0.0
"""

from datetime import datetime, timezone
from typing import Any, Dict

from domain.interfaces.iadmin_service import IAdminStatsService
from utils.logger import logger


class AdminStatsService(IAdminStatsService):
    """Servicio dedicado a estadísticas del panel de administración."""

    def __init__(
        self,
        user_repository,
        key_repository,
        payment_repository,
    ):
        self.user_repository = user_repository
        self.key_repository = key_repository
        self.payment_repository = payment_repository

    async def get_dashboard_stats(self, current_user_id: int) -> Dict:
        """
        Genera estadísticas completas para el panel de control administrativo.
        Centraliza la lógica de negocio para respetar arquitectura hexagonal.
        """
        try:
            users = await self.user_repository.get_all_users(current_user_id)
            all_keys = await self.key_repository.get_all_keys(current_user_id)

            total_users = len(users)
            active_users = sum(
                1
                for u in users
                if getattr(u, "status", "").lower() == "active"
                or getattr(u, "is_active", False)
            )

            total_keys = len(all_keys)
            active_keys = sum(1 for k in all_keys if k.is_active)
            wireguard_keys = sum(
                1
                for k in all_keys
                if hasattr(k.key_type, "value")
                and k.key_type.value.lower() == "wireguard"
                or str(k.key_type).lower() == "wireguard"
            )
            outline_keys = sum(
                1
                for k in all_keys
                if hasattr(k.key_type, "value")
                and k.key_type.value.lower() == "outline"
                or str(k.key_type).lower() == "outline"
            )

            wireguard_pct = round(
                (wireguard_keys / total_keys * 100) if total_keys > 0 else 0, 1
            )
            outline_pct = round(
                (outline_keys / total_keys * 100) if total_keys > 0 else 0, 1
            )

            total_usage_gb = 0
            avg_usage = round(total_usage_gb / total_users, 2) if total_users > 0 else 0

            total_revenue = await self._calculate_total_revenue()
            new_users_today = await self._calculate_new_users_today(current_user_id)
            keys_created_today = await self._calculate_keys_created_today(
                current_user_id
            )

            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_deposited": 0,
                "total_keys": total_keys,
                "active_keys": active_keys,
                "wireguard_keys": wireguard_keys,
                "wireguard_pct": wireguard_pct,
                "outline_keys": outline_keys,
                "outline_pct": outline_pct,
                "total_usage_gb": total_usage_gb,
                "avg_usage_gb": avg_usage,
                "total_revenue": total_revenue,
                "new_users_today": new_users_today,
                "keys_created_today": keys_created_today,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        except Exception as e:
            logger.error(f"Error generando estadísticas de dashboard: {e}")
            raise e

    async def _calculate_total_revenue(self) -> float:
        """Calcula los ingresos totales del sistema."""
        try:
            deposit_transactions = (
                await self.payment_repository.get_transactions_by_type("deposit")
            )
            total_amount = sum(t["amount"] for t in deposit_transactions)
            total_revenue = total_amount / 100.0
            return round(total_revenue, 2)
        except Exception as e:
            logger.error(f"Error calculando ingresos totales: {e}")
            return 0.00

    async def _calculate_new_users_today(self, current_user_id: int) -> int:
        """Calcula la cantidad de nuevos usuarios registrados hoy."""
        try:
            all_users = await self.user_repository.get_all_users(current_user_id)
            today = datetime.now(timezone.utc).date()
            new_users_today = sum(
                1
                for user in all_users
                if user.created_at and user.created_at.date() == today
            )
            return new_users_today
        except Exception as e:
            logger.error(f"Error calculando nuevos usuarios hoy: {e}")
            return 0

    async def _calculate_keys_created_today(self, current_user_id: int) -> int:
        """Calcula la cantidad de llaves VPN creadas hoy."""
        try:
            all_keys = await self.key_repository.get_all_keys(current_user_id)
            today = datetime.now(timezone.utc).date()
            keys_created_today = sum(
                1
                for key in all_keys
                if key.created_at and key.created_at.date() == today
            )
            return keys_created_today
        except Exception as e:
            logger.error(f"Error calculando llaves creadas hoy: {e}")
            return 0
