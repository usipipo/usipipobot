from datetime import datetime, timedelta
from typing import Optional

from pytz import UTC

from domain.entities.user import User, UserRole
from domain.interfaces.itransaction_repository import ITransactionRepository
from domain.interfaces.iuser_repository import IUserRepository
from utils.logger import logger


class PaymentService:
    def __init__(
        self, user_repo: IUserRepository, transaction_repo: ITransactionRepository
    ):
        self.user_repo = user_repo
        self.transaction_repo = transaction_repo

    async def update_balance(
        self,
        telegram_id: int,
        amount: int,
        transaction_type: str,
        description: str,
        reference_id: Optional[str] = None,
        telegram_payment_id: Optional[str] = None,
        current_user_id: Optional[int] = None,
    ) -> bool:
        """Actualiza el balance del usuario y registra la transacción."""
        try:
            uid = current_user_id or telegram_id
            user = await self.user_repo.get_by_id(telegram_id, uid)
            if not user:
                raise Exception("Usuario no encontrado")

            old_balance = user.balance_stars
            user.balance_stars += amount

            if amount > 0 and transaction_type == "deposit":
                user.total_deposited += amount

            await self.user_repo.save(user, uid)

            await self.transaction_repo.record_transaction(
                user_id=telegram_id,
                transaction_type=transaction_type,
                amount=amount,
                balance_after=user.balance_stars,
                description=description,
                reference_id=reference_id,
                telegram_payment_id=telegram_payment_id,
            )

            logger.info(
                f"💰 Balance updated for user {telegram_id}: {old_balance} -> {user.balance_stars}"
            )
            return True

        except Exception as e:
            logger.error(f"Error updating balance: {e}")
            return False

    async def apply_referral_commission(self, telegram_id: int, amount: int) -> bool:
        """Aplica comisión de referido al usuario que refirió a este."""
        try:
            user = await self.user_repo.get_by_id(telegram_id, telegram_id)
            if not user or not user.referred_by:
                return True

            referrer = await self.user_repo.get_by_id(user.referred_by, telegram_id)
            if not referrer:
                return True

            commission = int(amount * 0.10)

            referrer.balance_stars += commission
            referrer.total_referral_earnings += commission
            await self.user_repo.save(referrer, telegram_id)

            await self.transaction_repo.record_transaction(
                user_id=user.referred_by,
                transaction_type="referral_commission",
                amount=commission,
                balance_after=referrer.balance_stars,
                description=f"Comisión por referido: {user.telegram_id}",
                reference_id=f"ref_comm_{telegram_id}_{amount}",
            )

            logger.info(
                f"🎉 Referral commission applied: {commission} stars to {user.referred_by}"
            )
            return True

        except Exception as e:
            logger.error(f"Error applying referral commission: {e}")
            return False

    async def get_user_balance(self, telegram_id: int) -> Optional[int]:
        """Obtiene el balance de estrellas del usuario."""
        try:
            user = await self.user_repo.get_by_id(telegram_id, telegram_id)
            if not user:
                return None
            return user.balance_stars
        except Exception as e:
            logger.error(f"Error getting user balance: {e}")
            return None

    async def deduct_balance(
        self, telegram_id: int, amount: int, description: str = "Purchase"
    ) -> bool:
        """Deduce estrellas del balance del usuario."""
        try:
            user = await self.user_repo.get_by_id(telegram_id, telegram_id)
            if not user:
                raise Exception("Usuario no encontrado")

            if user.balance_stars < amount:
                raise Exception("Balance insuficiente")

            old_balance = user.balance_stars
            user.balance_stars -= amount

            await self.user_repo.save(user, telegram_id)

            await self.transaction_repo.record_transaction(
                user_id=telegram_id,
                transaction_type="purchase",
                amount=-amount,
                balance_after=user.balance_stars,
                description=description,
                reference_id=f"purchase_{telegram_id}_{datetime.now(UTC).timestamp()}",
            )

            logger.info(
                f"💰 Balance deducted for user {telegram_id}: {old_balance} -> {user.balance_stars}"
            )
            return True
        except Exception as e:
            logger.error(f"Error deducting balance: {e}")
            return False

    async def activate_vip(self, telegram_id: int, days: int = 30) -> bool:
        """Activa estado VIP para un usuario por N días."""
        try:
            user = await self.user_repo.get_by_id(telegram_id, telegram_id)
            if not user:
                raise Exception("Usuario no encontrado")

            user.is_vip = True
            user.vip_expires_at = datetime.now(UTC) + timedelta(days=days)

            await self.user_repo.save(user, telegram_id)
            logger.info(
                f"👑 VIP activated for user {telegram_id} until {user.vip_expires_at}"
            )
            return True
        except Exception as e:
            logger.error(f"Error activating VIP: {e}")
            return False

    async def add_storage(self, telegram_id: int, gb: int) -> bool:
        """Agrega almacenamiento adicional al usuario (en GB).
        
        NOTE: Este método será eliminado en la refactorización del modelo de negocio v2.0.
        El almacenamiento ahora se maneja a través de free_data_limit_bytes.
        """
        try:
            user = await self.user_repo.get_by_id(telegram_id, telegram_id)
            if not user:
                raise Exception("Usuario no encontrado")

            user.free_data_limit_bytes += gb * 1024**3

            await self.user_repo.save(user, telegram_id)
            logger.info(
                f"💾 Storage added to user {telegram_id}: +{gb}GB (Total: {user.free_data_limit_bytes // 1024**3}GB)"
            )
            return True
        except Exception as e:
            logger.error(f"Error adding storage: {e}")
            return False

    async def assign_role(
        self, telegram_id: int, role: UserRole, days: Optional[int] = None
    ) -> bool:
        """Asigna un rol especial al usuario (TASK_MANAGER o ANNOUNCER)."""
        try:
            user = await self.user_repo.get_by_id(telegram_id, telegram_id)
            if not user:
                raise Exception("Usuario no encontrado")

            user.role = role

            if days:
                expires_at = datetime.now(UTC) + timedelta(days=days)
                if role == UserRole.TASK_MANAGER:
                    user.task_manager_expires_at = expires_at
                elif role == UserRole.ANNOUNCER:
                    user.announcer_expires_at = expires_at

            await self.user_repo.save(user, telegram_id)
            logger.info(f"👤 Role {role} assigned to user {telegram_id}")
            return True
        except Exception as e:
            logger.error(f"Error assigning role: {e}")
            return False
