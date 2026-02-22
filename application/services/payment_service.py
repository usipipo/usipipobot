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

    async def record_transaction(
        self,
        telegram_id: int,
        amount: int,
        transaction_type: str,
        description: str,
        reference_id: Optional[str] = None,
        telegram_payment_id: Optional[str] = None,
        current_user_id: Optional[int] = None,
    ) -> bool:
        """Registra una transacción sin mantener balance acumulativo."""
        try:
            uid = current_user_id or telegram_id
            user = await self.user_repo.get_by_id(telegram_id, uid)
            if not user:
                raise Exception("Usuario no encontrado")

            await self.transaction_repo.record_transaction(
                user_id=telegram_id,
                transaction_type=transaction_type,
                amount=amount,
                balance_after=0,
                description=description,
                reference_id=reference_id,
                telegram_payment_id=telegram_payment_id,
            )

            logger.info(f"💰 Transaction recorded for user {telegram_id}: {amount} stars - {transaction_type}")
            return True

        except Exception as e:
            logger.error(f"Error recording transaction: {e}")
            return False

    async def apply_referral_credits(self, telegram_id: int, credits: int) -> bool:
        """Aplica créditos de referido al usuario que refirió a este."""
        try:
            user = await self.user_repo.get_by_id(telegram_id, telegram_id)
            if not user or not user.referred_by:
                return True

            referrer = await self.user_repo.get_by_id(user.referred_by, telegram_id)
            if not referrer:
                return True

            referrer.referral_credits += credits
            await self.user_repo.save(referrer, telegram_id)

            await self.transaction_repo.record_transaction(
                user_id=user.referred_by,
                transaction_type="referral_credits",
                amount=credits,
                balance_after=referrer.referral_credits,
                description=f"Créditos por referido: {user.telegram_id}",
                reference_id=f"ref_credits_{telegram_id}",
            )

            logger.info(
                f"🎉 Referral credits applied: {credits} credits to {user.referred_by}"
            )
            return True

        except Exception as e:
            logger.error(f"Error applying referral credits: {e}")
            return False

    async def get_user_credits(self, telegram_id: int) -> Optional[int]:
        """Obtiene los créditos de referido del usuario."""
        try:
            user = await self.user_repo.get_by_id(telegram_id, telegram_id)
            if not user:
                return None
            return user.referral_credits
        except Exception as e:
            logger.error(f"Error getting user credits: {e}")
            return None

    async def redeem_credits(
        self, telegram_id: int, credits: int, description: str = "Credit redemption"
    ) -> bool:
        """Canjea créditos del usuario."""
        try:
            user = await self.user_repo.get_by_id(telegram_id, telegram_id)
            if not user:
                raise Exception("Usuario no encontrado")

            if user.referral_credits < credits:
                raise Exception("Créditos insuficientes")

            user.referral_credits -= credits
            await self.user_repo.save(user, telegram_id)

            await self.transaction_repo.record_transaction(
                user_id=telegram_id,
                transaction_type="credit_redemption",
                amount=-credits,
                balance_after=user.referral_credits,
                description=description,
                reference_id=f"redeem_{telegram_id}_{datetime.now(UTC).timestamp()}",
            )

            logger.info(
                f"💳 Credits redeemed for user {telegram_id}: -{credits} (remaining: {user.referral_credits})"
            )
            return True
        except Exception as e:
            logger.error(f"Error redeeming credits: {e}")
            return False

    async def add_storage(self, telegram_id: int, gb: int) -> bool:
        """Agrega almacenamiento adicional al usuario (en GB)."""
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
