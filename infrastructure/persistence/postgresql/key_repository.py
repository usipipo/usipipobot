"""
Repositorio de llaves VPN con SQLAlchemy Async para PostgreSQL.

Author: uSipipo Team
Version: 2.1.0
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.vpn_key import KeyType, VpnKey
from domain.interfaces.ikey_repository import IKeyRepository
from utils.logger import logger

from .base_repository import BasePostgresRepository
from .models import VpnKeyModel


def _normalize_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class PostgresKeyRepository(BasePostgresRepository, IKeyRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    def _model_to_entity(self, model: VpnKeyModel) -> VpnKey:
        return VpnKey(
            id=model.id,
            user_id=model.user_id,
            key_type=KeyType(model.key_type) if model.key_type else KeyType.OUTLINE,
            name=model.name,
            key_data=model.key_data,
            external_id=model.external_id,
            created_at=_normalize_datetime(model.created_at)
            or datetime.now(timezone.utc),
            is_active=model.is_active,
            used_bytes=model.used_bytes or 0,
            last_seen_at=_normalize_datetime(model.last_seen_at),
            data_limit_bytes=model.data_limit_bytes or 10 * 1024**3,
            billing_reset_at=_normalize_datetime(model.billing_reset_at)
            or datetime.now(timezone.utc),
        )

    def _entity_to_model(self, entity: VpnKey) -> VpnKeyModel:
        return VpnKeyModel(
            id=entity.id if entity.id else uuid.uuid4(),
            user_id=entity.user_id,
            key_type=(
                entity.key_type.value
                if isinstance(entity.key_type, KeyType)
                else entity.key_type
            ),
            name=entity.name,
            key_data=entity.key_data,
            external_id=entity.external_id,
            is_active=entity.is_active,
            used_bytes=entity.used_bytes,
            last_seen_at=entity.last_seen_at,
            data_limit_bytes=entity.data_limit_bytes,
            billing_reset_at=entity.billing_reset_at,
        )

    async def save(self, key: VpnKey, current_user_id: int) -> VpnKey:
        await self._set_current_user(current_user_id)
        try:
            if key.id:
                existing = await self.session.get(VpnKeyModel, key.id)
                if existing:
                    existing.name, existing.key_data, existing.external_id = (
                        key.name,
                        key.key_data,
                        key.external_id,
                    )
                    existing.is_active, existing.used_bytes, existing.last_seen_at = (
                        key.is_active,
                        key.used_bytes,
                        key.last_seen_at,
                    )
                    existing.data_limit_bytes, existing.billing_reset_at = (
                        key.data_limit_bytes,
                        key.billing_reset_at,
                    )
                else:
                    self.session.add(self._entity_to_model(key))
            else:
                key.id = uuid.uuid4()
                self.session.add(self._entity_to_model(key))
            await self.session.commit()
            logger.debug(f"Llave {key.id} guardada correctamente.")
            return key
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al guardar llave: {e}")
            raise

    async def get_by_user_id(
        self, telegram_id: int, current_user_id: int
    ) -> List[VpnKey]:
        await self._set_current_user(current_user_id)
        try:
            query = select(VpnKeyModel).where(
                VpnKeyModel.user_id == telegram_id, VpnKeyModel.is_active == True
            )
            result = await self.session.execute(query)
            return [self._model_to_entity(m) for m in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error al listar llaves del usuario {telegram_id}: {e}")
            return []

    async def get_by_user(self, telegram_id: int, current_user_id: int) -> List[VpnKey]:
        return await self.get_by_user_id(telegram_id, current_user_id)

    async def get_all_active(self, current_user_id: int) -> List[VpnKey]:
        await self._set_current_user(current_user_id)
        try:
            query = select(VpnKeyModel).where(VpnKeyModel.is_active == True)
            result = await self.session.execute(query)
            return [self._model_to_entity(m) for m in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error al obtener llaves activas: {e}")
            return []

    async def get_all_keys(self, current_user_id: int) -> List[VpnKey]:
        await self._set_current_user(current_user_id)
        try:
            query = select(VpnKeyModel)
            result = await self.session.execute(query)
            return [self._model_to_entity(m) for m in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error al obtener todas las llaves: {e}")
            return []

    async def get_by_id(
        self, key_id: uuid.UUID, current_user_id: int
    ) -> Optional[VpnKey]:
        await self._set_current_user(current_user_id)
        try:
            model = await self.session.get(VpnKeyModel, key_id)
            return self._model_to_entity(model) if model else None
        except Exception as e:
            logger.error(f"Error al obtener llave {key_id}: {e}")
            return None

    async def delete(self, key_id: uuid.UUID, current_user_id: int) -> bool:
        await self._set_current_user(current_user_id)
        try:
            query = (
                update(VpnKeyModel)
                .where(VpnKeyModel.id == key_id)
                .values(is_active=False)
            )
            await self.session.execute(query)
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al eliminar llave {key_id}: {e}")
            return False

    async def update_usage(
        self, key_id: uuid.UUID, used_bytes: int, current_user_id: int
    ) -> bool:
        await self._set_current_user(current_user_id)
        try:
            query = (
                update(VpnKeyModel)
                .where(VpnKeyModel.id == key_id)
                .values(used_bytes=used_bytes, last_seen_at=datetime.now(timezone.utc))
            )
            await self.session.execute(query)
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al actualizar uso de llave {key_id}: {e}")
            return False

    async def update_data_limit(
        self, key_id: uuid.UUID, data_limit_bytes: int, current_user_id: int
    ) -> bool:
        await self._set_current_user(current_user_id)
        try:
            query = (
                update(VpnKeyModel)
                .where(VpnKeyModel.id == key_id)
                .values(data_limit_bytes=data_limit_bytes)
            )
            await self.session.execute(query)
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al actualizar limite de datos: {e}")
            return False

    async def reset_data_usage(self, key_id: uuid.UUID, current_user_id: int) -> bool:
        await self._set_current_user(current_user_id)
        try:
            query = (
                update(VpnKeyModel)
                .where(VpnKeyModel.id == key_id)
                .values(used_bytes=0, billing_reset_at=datetime.now(timezone.utc))
            )
            await self.session.execute(query)
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al resetear uso de datos: {e}")
            return False

    async def get_keys_needing_reset(self, current_user_id: int) -> List[VpnKey]:
        await self._set_current_user(current_user_id)
        try:
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            query = select(VpnKeyModel).where(
                VpnKeyModel.billing_reset_at < thirty_days_ago,
                VpnKeyModel.is_active == True,
            )
            result = await self.session.execute(query)
            return [self._model_to_entity(m) for m in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error al obtener llaves para reset: {e}")
            return []
