"""
Repositorio de usuarios con SQLAlchemy Async para PostgreSQL.

Author: uSipipo Team
Version: 2.1.0
"""

import secrets
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.user import User, UserRole, UserStatus
from domain.interfaces.iuser_repository import IUserRepository
from utils.logger import logger

from .base_repository import BasePostgresRepository
from .models import UserModel


class PostgresUserRepository(BasePostgresRepository, IUserRepository):
    """
    Implementación del repositorio de usuarios usando SQLAlchemy Async con PostgreSQL.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    def _model_to_entity(self, model: UserModel) -> User:
        return User(
            telegram_id=model.telegram_id,
            username=model.username,
            full_name=model.full_name,
            status=UserStatus(model.status) if model.status else UserStatus.ACTIVE,
            role=UserRole(model.role) if model.role else UserRole.USER,
            max_keys=model.max_keys or 2,
            referral_code=model.referral_code,
            referred_by=model.referred_by,
            referral_credits=model.referral_credits or 0,
            free_data_limit_bytes=model.free_data_limit_bytes or 5 * 1024**3,
            free_data_used_bytes=model.free_data_used_bytes or 0,
            wallet_address=model.wallet_address,
            purchase_count=model.purchase_count or 0,
            loyalty_bonus_percent=model.loyalty_bonus_percent or 0,
            welcome_bonus_used=model.welcome_bonus_used or False,
            referred_users_with_purchase=model.referred_users_with_purchase or 0,
            created_at=model.created_at,
        )

    def _entity_to_model(self, entity: User) -> UserModel:
        return UserModel(
            telegram_id=entity.telegram_id,
            username=entity.username,
            full_name=entity.full_name,
            status=(
                entity.status.value
                if isinstance(entity.status, UserStatus)
                else entity.status
            ),
            role=(
                entity.role.value if isinstance(entity.role, UserRole) else entity.role
            ),
            max_keys=entity.max_keys,
            referral_code=entity.referral_code,
            referred_by=entity.referred_by,
            referral_credits=entity.referral_credits,
            free_data_limit_bytes=entity.free_data_limit_bytes,
            free_data_used_bytes=entity.free_data_used_bytes,
            wallet_address=entity.wallet_address,
            purchase_count=entity.purchase_count,
            loyalty_bonus_percent=entity.loyalty_bonus_percent,
            welcome_bonus_used=entity.welcome_bonus_used,
            referred_users_with_purchase=entity.referred_users_with_purchase,
        )

    async def get_by_id(self, telegram_id: int, current_user_id: int) -> Optional[User]:
        await self._set_current_user(current_user_id)
        try:
            query = select(UserModel).where(UserModel.telegram_id == telegram_id)
            result = await self.session.execute(query)
            model = result.scalar_one_or_none()
            return self._model_to_entity(model) if model else None
        except Exception as e:
            logger.error(f"Error al obtener usuario {telegram_id}: {e}")
            return None

    async def save(self, user: User, current_user_id: int) -> User:
        await self._set_current_user(current_user_id)
        try:
            existing = await self.session.get(UserModel, user.telegram_id)
            if existing:
                existing.username = user.username
                existing.full_name = user.full_name
                existing.status = (
                    user.status.value
                    if isinstance(user.status, UserStatus)
                    else user.status
                )
                existing.role = (
                    user.role.value if isinstance(user.role, UserRole) else user.role
                )
                existing.max_keys = user.max_keys
                existing.referral_code = user.referral_code
                existing.referred_by = user.referred_by
                existing.referral_credits = user.referral_credits
                existing.free_data_limit_bytes = user.free_data_limit_bytes
                existing.free_data_used_bytes = user.free_data_used_bytes
                existing.wallet_address = user.wallet_address
                existing.purchase_count = user.purchase_count
                existing.loyalty_bonus_percent = user.loyalty_bonus_percent
                existing.welcome_bonus_used = user.welcome_bonus_used
                existing.referred_users_with_purchase = (
                    user.referred_users_with_purchase
                )
            else:
                model = self._entity_to_model(user)
                self.session.add(model)
            await self.session.commit()
            logger.info(f"Usuario {user.telegram_id} guardado correctamente.")
            return user
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al guardar usuario: {e}")
            raise

    async def create_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        referral_code: Optional[str] = None,
        referred_by: Optional[int] = None,
        current_user_id: Optional[int] = None,
    ) -> User:
        if referral_code is None:
            referral_code = secrets.token_hex(4).upper()
        user = User(
            telegram_id=user_id,
            username=username,
            full_name=full_name,
            referral_code=referral_code,
            referred_by=referred_by,
        )
        if current_user_id is None:
            current_user_id = user_id
        return await self.save(user, current_user_id)

    async def exists(self, telegram_id: int, current_user_id: int) -> bool:
        await self._set_current_user(current_user_id)
        try:
            query = select(UserModel.telegram_id).where(
                UserModel.telegram_id == telegram_id
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error verificando existencia de usuario: {e}")
            return False

    async def get_by_referral_code(
        self, referral_code: str, current_user_id: int
    ) -> Optional[User]:
        await self._set_current_user(current_user_id)
        try:
            query = select(UserModel).where(UserModel.referral_code == referral_code)
            result = await self.session.execute(query)
            model = result.scalar_one_or_none()
            return self._model_to_entity(model) if model else None
        except Exception as e:
            logger.error(f"Error al buscar por referral_code {referral_code}: {e}")
            return None

    async def get_referrals(self, referrer_id: int, current_user_id: int) -> List[dict]:
        await self._set_current_user(current_user_id)
        try:
            query = select(UserModel).where(UserModel.referred_by == referrer_id)
            result = await self.session.execute(query)
            models = result.scalars().all()
            return [
                {
                    "telegram_id": m.telegram_id,
                    "username": m.username,
                    "full_name": m.full_name,
                    "created_at": m.created_at,
                }
                for m in models
            ]
        except Exception as e:
            logger.error(f"Error al obtener referidos: {e}")
            return []

    async def get_referrals_by_user(
        self, telegram_id: int, current_user_id: int
    ) -> List[User]:
        await self._set_current_user(current_user_id)
        try:
            query = select(UserModel).where(UserModel.referred_by == telegram_id)
            result = await self.session.execute(query)
            models = result.scalars().all()
            return [self._model_to_entity(m) for m in models]
        except Exception as e:
            logger.error(f"Error al obtener referidos por usuario {telegram_id}: {e}")
            return []

    async def get_all_users(self, current_user_id: int) -> List[User]:
        await self._set_current_user(current_user_id)
        try:
            query = select(UserModel)
            result = await self.session.execute(query)
            models = result.scalars().all()
            return [self._model_to_entity(m) for m in models]
        except Exception as e:
            logger.error(f"Error al obtener todos los usuarios: {e}")
            return []

    async def update_free_data_usage(
        self, telegram_id: int, bytes_used: int, current_user_id: int
    ) -> bool:
        """Actualiza el uso de datos gratuitos de un usuario."""
        await self._set_current_user(current_user_id)
        try:
            query = (
                update(UserModel)
                .where(UserModel.telegram_id == telegram_id)
                .values(
                    free_data_used_bytes=UserModel.free_data_used_bytes + bytes_used
                )
            )
            await self.session.execute(query)
            await self.session.commit()
            logger.debug(
                f"Uso de datos gratuitos actualizado para usuario {telegram_id}"
            )
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al actualizar uso de datos gratuitos: {e}")
            return False

    async def update_referral_credits(
        self, telegram_id: int, credits_delta: int, current_user_id: int
    ) -> bool:
        """Actualiza los créditos de referido de un usuario."""
        await self._set_current_user(current_user_id)
        try:
            query = (
                update(UserModel)
                .where(UserModel.telegram_id == telegram_id)
                .values(referral_credits=UserModel.referral_credits + credits_delta)
            )
            await self.session.execute(query)
            await self.session.commit()
            logger.debug(
                f"Créditos actualizados para usuario {telegram_id}: {credits_delta:+d}"
            )
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al actualizar créditos de referido: {e}")
            return False

    async def increment_max_keys(
        self, telegram_id: int, slots: int, current_user_id: int
    ) -> bool:
        """Incrementa el límite de claves de un usuario."""
        await self._set_current_user(current_user_id)
        try:
            query = (
                update(UserModel)
                .where(UserModel.telegram_id == telegram_id)
                .values(max_keys=UserModel.max_keys + slots)
            )
            await self.session.execute(query)
            await self.session.commit()
            logger.debug(
                f"Límite de claves incrementado para usuario {telegram_id}: +{slots}"
            )
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al incrementar límite de claves: {e}")
            return False

    async def update_user(self, user: User) -> User:
        """Actualiza un usuario existente."""
        try:
            existing = await self.session.get(UserModel, user.telegram_id)
            if existing:
                existing.username = user.username
                existing.full_name = user.full_name
                existing.status = (
                    user.status.value
                    if isinstance(user.status, UserStatus)
                    else user.status
                )
                existing.role = (
                    user.role.value if isinstance(user.role, UserRole) else user.role
                )
                existing.max_keys = user.max_keys
                existing.referral_code = user.referral_code
                existing.referred_by = user.referred_by
                existing.referral_credits = user.referral_credits
                existing.free_data_limit_bytes = user.free_data_limit_bytes
                existing.free_data_used_bytes = user.free_data_used_bytes
                existing.wallet_address = user.wallet_address
                await self.session.commit()
                logger.info(f"Usuario {user.telegram_id} actualizado correctamente.")
                return user
            else:
                raise ValueError(f"Usuario {user.telegram_id} no encontrado")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al actualizar usuario: {e}")
            raise

    async def get_by_wallet_address(
        self, wallet_address: str, current_user_id: int
    ) -> Optional[User]:
        """Busca un usuario por su dirección de wallet BSC."""
        await self._set_current_user(current_user_id)
        try:
            query = select(UserModel).where(UserModel.wallet_address == wallet_address)
            result = await self.session.execute(query)
            model = result.scalar_one_or_none()
            return self._model_to_entity(model) if model else None
        except Exception as e:
            logger.error(f"Error al buscar por wallet address {wallet_address}: {e}")
            return None

    async def update_wallet_address(
        self, telegram_id: int, wallet_address: str, current_user_id: int
    ) -> bool:
        """Actualiza la dirección de wallet de un usuario."""
        await self._set_current_user(current_user_id)
        try:
            query = (
                update(UserModel)
                .where(UserModel.telegram_id == telegram_id)
                .values(wallet_address=wallet_address)
            )
            await self.session.execute(query)
            await self.session.commit()
            logger.debug(
                f"Wallet address actualizada para usuario {telegram_id}: {wallet_address}"
            )
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al actualizar wallet address: {e}")
            return False

    async def delete_user(self, telegram_id: int) -> bool:
        """Elimina un usuario de la base de datos."""
        try:
            existing = await self.session.get(UserModel, telegram_id)
            if existing:
                await self.session.delete(existing)
                await self.session.commit()
                logger.info(f"Usuario {telegram_id} eliminado correctamente.")
                return True
            else:
                logger.warning(f"Usuario {telegram_id} no encontrado para eliminar.")
                return False
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al eliminar usuario {telegram_id}: {e}")
            raise
