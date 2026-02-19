"""
Repositorio de paquetes de datos con SQLAlchemy Async para PostgreSQL.

Author: uSipipo Team
Version: 2.1.0
"""

from typing import List, Optional
from datetime import datetime, timezone
import uuid

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger import logger

from domain.entities.data_package import DataPackage, PackageType
from domain.interfaces.idata_package_repository import IDataPackageRepository
from .models import DataPackageModel
from .base_repository import BasePostgresRepository


def _normalize_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class PostgresDataPackageRepository(BasePostgresRepository, IDataPackageRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    def _model_to_entity(self, model: DataPackageModel) -> DataPackage:
        return DataPackage(
            id=model.id,
            user_id=model.user_id,
            package_type=PackageType(model.package_type),
            data_limit_bytes=model.data_limit_bytes,
            data_used_bytes=model.data_used_bytes or 0,
            stars_paid=model.stars_paid,
            purchased_at=_normalize_datetime(model.purchased_at) or datetime.now(timezone.utc),
            expires_at=_normalize_datetime(model.expires_at) or datetime.now(timezone.utc),
            is_active=model.is_active,
            telegram_payment_id=model.telegram_payment_id
        )

    def _entity_to_model(self, entity: DataPackage) -> DataPackageModel:
        return DataPackageModel(
            id=entity.id if entity.id else uuid.uuid4(),
            user_id=entity.user_id,
            package_type=entity.package_type.value if isinstance(entity.package_type, PackageType) else entity.package_type,
            data_limit_bytes=entity.data_limit_bytes,
            data_used_bytes=entity.data_used_bytes,
            stars_paid=entity.stars_paid,
            purchased_at=entity.purchased_at,
            expires_at=entity.expires_at,
            is_active=entity.is_active,
            telegram_payment_id=entity.telegram_payment_id
        )

    async def save(self, data_package: DataPackage, current_user_id: int) -> DataPackage:
        await self._set_current_user(current_user_id)
        try:
            if data_package.id:
                existing = await self.session.get(DataPackageModel, data_package.id)
                if existing:
                    existing.package_type = data_package.package_type.value if isinstance(data_package.package_type, PackageType) else data_package.package_type
                    existing.data_limit_bytes = data_package.data_limit_bytes
                    existing.data_used_bytes = data_package.data_used_bytes
                    existing.stars_paid = data_package.stars_paid
                    existing.expires_at = data_package.expires_at
                    existing.is_active = data_package.is_active
                    existing.telegram_payment_id = data_package.telegram_payment_id
                else:
                    self.session.add(self._entity_to_model(data_package))
            else:
                data_package.id = uuid.uuid4()
                self.session.add(self._entity_to_model(data_package))
            await self.session.commit()
            logger.debug(f"Paquete de datos {data_package.id} guardado correctamente.")
            return data_package
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al guardar paquete de datos: {e}")
            raise

    async def get_by_id(self, package_id: uuid.UUID, current_user_id: int) -> Optional[DataPackage]:
        await self._set_current_user(current_user_id)
        try:
            model = await self.session.get(DataPackageModel, package_id)
            return self._model_to_entity(model) if model else None
        except Exception as e:
            logger.error(f"Error al obtener paquete {package_id}: {e}")
            return None

    async def get_by_user(self, telegram_id: int, current_user_id: int) -> List[DataPackage]:
        await self._set_current_user(current_user_id)
        try:
            query = select(DataPackageModel).where(DataPackageModel.user_id == telegram_id)
            result = await self.session.execute(query)
            return [self._model_to_entity(m) for m in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error al listar paquetes del usuario {telegram_id}: {e}")
            return []

    async def get_active_by_user(self, telegram_id: int, current_user_id: int) -> List[DataPackage]:
        await self._set_current_user(current_user_id)
        try:
            query = select(DataPackageModel).where(
                DataPackageModel.user_id == telegram_id,
                DataPackageModel.is_active == True
            )
            result = await self.session.execute(query)
            return [self._model_to_entity(m) for m in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error al obtener paquetes activos del usuario {telegram_id}: {e}")
            return []

    async def get_valid_by_user(self, telegram_id: int, current_user_id: int) -> List[DataPackage]:
        await self._set_current_user(current_user_id)
        try:
            now = datetime.now(timezone.utc)
            query = select(DataPackageModel).where(
                DataPackageModel.user_id == telegram_id,
                DataPackageModel.is_active == True,
                DataPackageModel.expires_at > now
            )
            result = await self.session.execute(query)
            return [self._model_to_entity(m) for m in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error al obtener paquetes validos del usuario {telegram_id}: {e}")
            return []

    async def update_usage(self, package_id: uuid.UUID, bytes_used: int, current_user_id: int) -> bool:
        await self._set_current_user(current_user_id)
        try:
            query = update(DataPackageModel).where(
                DataPackageModel.id == package_id
            ).values(
                data_used_bytes=DataPackageModel.data_used_bytes + bytes_used
            )
            await self.session.execute(query)
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al actualizar uso del paquete {package_id}: {e}")
            return False

    async def deactivate(self, package_id: uuid.UUID, current_user_id: int) -> bool:
        await self._set_current_user(current_user_id)
        try:
            query = update(DataPackageModel).where(
                DataPackageModel.id == package_id
            ).values(is_active=False)
            await self.session.execute(query)
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al desactivar paquete {package_id}: {e}")
            return False

    async def delete(self, package_id: uuid.UUID, current_user_id: int) -> bool:
        await self._set_current_user(current_user_id)
        try:
            query = delete(DataPackageModel).where(DataPackageModel.id == package_id)
            await self.session.execute(query)
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al eliminar paquete {package_id}: {e}")
            return False
