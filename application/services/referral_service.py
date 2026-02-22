"""
Servicio de gestión de referidos y créditos.

Author: uSipipo Team
Version: 1.0.0
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from config import settings
from domain.entities.user import User
from domain.interfaces.itransaction_repository import ITransactionRepository
from domain.interfaces.iuser_repository import IUserRepository
from utils.logger import logger


@dataclass
class ReferralStats:
    """Estadísticas de referidos de un usuario."""
    referral_code: str
    total_referrals: int
    referral_credits: int
    referred_by: Optional[int]


class ReferralService:
    """
    Servicio para gestión del sistema de referidos.
    
    Maneja el registro de referidos, créditos y canjes.
    """

    def __init__(
        self,
        user_repo: IUserRepository,
        transaction_repo: ITransactionRepository,
    ):
        self.user_repo = user_repo
        self.transaction_repo = transaction_repo

    async def register_referral(
        self,
        new_user_id: int,
        referral_code: str,
        current_user_id: int,
    ) -> Dict[str, Any]:
        """
        Registra un nuevo referido y otorga créditos.
        
        Args:
            new_user_id: ID del nuevo usuario
            referral_code: Código de referido
            current_user_id: ID del usuario que ejecuta la acción
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            referrer = await self.user_repo.get_by_referral_code(
                referral_code, current_user_id
            )
            
            if not referrer:
                logger.warning(f"Código de referido no encontrado: {referral_code}")
                return {"success": False, "error": "invalid_code"}
            
            if referrer.telegram_id == new_user_id:
                logger.warning(f"Usuario intentó usarse a sí mismo como referidor")
                return {"success": False, "error": "self_referral"}
            
            new_user = await self.user_repo.get_by_id(new_user_id, current_user_id)
            if not new_user:
                return {"success": False, "error": "user_not_found"}
            
            if new_user.referred_by is not None:
                logger.info(f"Usuario {new_user_id} ya tiene referidor")
                return {"success": False, "error": "already_referred"}
            
            credits_for_referrer = settings.REFERRAL_CREDITS_PER_REFERRAL
            credits_for_new_user = settings.REFERRAL_BONUS_NEW_USER
            
            new_user.referred_by = referrer.telegram_id
            await self.user_repo.save(new_user, current_user_id)
            
            await self.user_repo.update_referral_credits(
                referrer.telegram_id, credits_for_referrer, current_user_id
            )
            
            await self.user_repo.update_referral_credits(
                new_user_id, credits_for_new_user, current_user_id
            )
            
            await self.transaction_repo.record_transaction(
                user_id=referrer.telegram_id,
                transaction_type="referral_bonus",
                amount=credits_for_referrer,
                balance_after=referrer.referral_credits + credits_for_referrer,
                description=f"Créditos por referido: nuevo usuario {new_user_id}",
                reference_id=f"ref_{new_user_id}_{referrer.telegram_id}",
            )
            
            logger.info(
                f"🎉 Referido registrado: {referrer.telegram_id} -> {new_user_id} "
                f"(+{credits_for_referrer} créditos)"
            )
            
            return {
                "success": True,
                "referrer_id": referrer.telegram_id,
                "credits_to_referrer": credits_for_referrer,
                "credits_to_new_user": credits_for_new_user,
            }
            
        except Exception as e:
            logger.error(f"Error registrando referido: {e}")
            return {"success": False, "error": str(e)}

    async def get_referral_stats(
        self, user_id: int, current_user_id: int
    ) -> ReferralStats:
        """
        Obtiene las estadísticas de referidos de un usuario.
        
        Args:
            user_id: ID del usuario
            current_user_id: ID del usuario que ejecuta la acción
            
        Returns:
            ReferralStats con estadísticas
        """
        user = await self.user_repo.get_by_id(user_id, current_user_id)
        if not user:
            raise ValueError(f"Usuario no encontrado: {user_id}")
        
        referrals = await self.user_repo.get_referrals_by_user(user_id, current_user_id)
        
        return ReferralStats(
            referral_code=user.referral_code or "",
            total_referrals=len(referrals),
            referral_credits=user.referral_credits,
            referred_by=user.referred_by,
        )

    async def redeem_credits_for_data(
        self, user_id: int, credits: int, current_user_id: int
    ) -> Dict[str, Any]:
        """
        Canjea créditos por datos adicionales.
        
        Args:
            user_id: ID del usuario
            credits: Cantidad de créditos a canjear
            current_user_id: ID del usuario que ejecuta la acción
            
        Returns:
            Dict con resultado del canje
        """
        try:
            user = await self.user_repo.get_by_id(user_id, current_user_id)
            if not user:
                return {"success": False, "error": "user_not_found"}
            
            if user.referral_credits < credits:
                return {"success": False, "error": "insufficient_credits"}
            
            credits_per_gb = settings.REFERRAL_CREDITS_PER_GB
            gb_to_add = credits // credits_per_gb
            
            if gb_to_add < 1:
                return {
                    "success": False,
                    "error": "insufficient_credits_for_gb",
                    "required": credits_per_gb,
                }
            
            actual_credits = gb_to_add * credits_per_gb
            
            await self.user_repo.update_referral_credits(
                user_id, -actual_credits, current_user_id
            )
            
            user.free_data_limit_bytes += gb_to_add * (1024**3)
            await self.user_repo.save(user, current_user_id)
            
            await self.transaction_repo.record_transaction(
                user_id=user_id,
                transaction_type="credit_redemption_data",
                amount=-actual_credits,
                balance_after=user.referral_credits - actual_credits,
                description=f"Canje de créditos: +{gb_to_add}GB",
                reference_id=f"redeem_data_{user_id}",
            )
            
            logger.info(
                f"💳 Créditos canjeados por datos: user {user_id}, "
                f"-{actual_credits} créditos, +{gb_to_add}GB"
            )
            
            return {
                "success": True,
                "credits_spent": actual_credits,
                "gb_added": gb_to_add,
                "remaining_credits": user.referral_credits - actual_credits,
            }
            
        except Exception as e:
            logger.error(f"Error canjeando créditos por datos: {e}")
            return {"success": False, "error": str(e)}

    async def redeem_credits_for_slot(
        self, user_id: int, current_user_id: int
    ) -> Dict[str, Any]:
        """
        Canjea créditos por un slot de clave adicional.
        
        Args:
            user_id: ID del usuario
            current_user_id: ID del usuario que ejecuta la acción
            
        Returns:
            Dict con resultado del canje
        """
        try:
            user = await self.user_repo.get_by_id(user_id, current_user_id)
            if not user:
                return {"success": False, "error": "user_not_found"}
            
            credits_per_slot = settings.REFERRAL_CREDITS_PER_SLOT
            
            if user.referral_credits < credits_per_slot:
                return {
                    "success": False,
                    "error": "insufficient_credits",
                    "required": credits_per_slot,
                    "current": user.referral_credits,
                }
            
            await self.user_repo.update_referral_credits(
                user_id, -credits_per_slot, current_user_id
            )
            
            await self.user_repo.increment_max_keys(user_id, 1, current_user_id)
            
            await self.transaction_repo.record_transaction(
                user_id=user_id,
                transaction_type="credit_redemption_slot",
                amount=-credits_per_slot,
                balance_after=user.referral_credits - credits_per_slot,
                description="Canje de créditos: +1 slot de clave",
                reference_id=f"redeem_slot_{user_id}",
            )
            
            logger.info(
                f"💳 Créditos canjeados por slot: user {user_id}, "
                f"-{credits_per_slot} créditos, +1 slot"
            )
            
            return {
                "success": True,
                "credits_spent": credits_per_slot,
                "slots_added": 1,
                "remaining_credits": user.referral_credits - credits_per_slot,
            }
            
        except Exception as e:
            logger.error(f"Error canjeando créditos por slot: {e}")
            return {"success": False, "error": str(e)}
