"""
Script de migración: Actualizar límite de datos de llaves VPN de 10GB a 5GB.

Este script actualiza todas las llaves VPN existentes que tengan un límite
de 10GB (10737418240 bytes) a 5GB (5368709120 bytes).

Uso:
    python scripts/migrate_key_data_limit_10gb_to_5gb.py

Author: uSipipo Team
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from infrastructure.persistence.postgresql.models import VpnKeyModel
from utils.logger import logger

# Constantes
OLD_LIMIT_BYTES = 10 * 1024**3  # 10 GB
NEW_LIMIT_BYTES = 5 * 1024**3  # 5 GB


async def migrate_key_data_limits():
    """
    Migra todas las llaves con límite de 10GB a 5GB.
    """
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Contar llaves que serán actualizadas
            count_result = await session.execute(
                select(VpnKeyModel).where(VpnKeyModel.data_limit_bytes == OLD_LIMIT_BYTES)
            )
            keys_to_update = count_result.scalars().all()
            total_keys = len(keys_to_update)

            if total_keys == 0:
                logger.info("✅ No hay llaves con límite de 10GB para actualizar.")
                return

            logger.info(f"📝 Encontradas {total_keys} llaves con límite de 10GB")

            # Mostrar algunas llaves de ejemplo
            for key in keys_to_update[:5]:
                logger.info(f"   - ID: {key.id}, Nombre: {key.name}, User: {key.user_id}")

            if total_keys > 5:
                logger.info(f"   ... y {total_keys - 5} más")

            # Confirmar antes de actualizar
            confirm = input(f"\n¿Actualizar {total_keys} llaves de 10GB a 5GB? (yes/no): ")
            if confirm.lower() != "yes":
                logger.info("❌ Migración cancelada por el usuario.")
                return

            # Ejecutar actualización
            result = await session.execute(
                update(VpnKeyModel)
                .where(VpnKeyModel.data_limit_bytes == OLD_LIMIT_BYTES)
                .values(data_limit_bytes=NEW_LIMIT_BYTES)
            )

            await session.commit()

            updated_count = result.rowcount if result.rowcount is not None else total_keys
            logger.info(
                f"✅ Migración completada: {updated_count} llaves actualizadas de 10GB a 5GB"
            )

            # Verificar que no queden llaves con 10GB
            verify_result = await session.execute(
                select(VpnKeyModel).where(VpnKeyModel.data_limit_bytes == OLD_LIMIT_BYTES)
            )
            remaining = len(verify_result.scalars().all())

            if remaining == 0:
                logger.info("✅ Verificación exitosa: No quedan llaves con 10GB")
            else:
                logger.warning(f"⚠️ Verificación: Aún quedan {remaining} llaves con 10GB")

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error durante la migración: {e}")
            raise
        finally:
            await session.close()

    await engine.dispose()


async def rollback_migration():
    """
    Revierte la migración: cambia llaves de 5GB de vuelta a 10GB.
    Útil en caso de emergencia.
    """
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            confirm = input("⚠️ ¿REVERTIR migración? Esto cambiará llaves de 5GB a 10GB (yes/no): ")
            if confirm.lower() != "yes":
                logger.info("❌ Rollback cancelado.")
                return

            result = await session.execute(
                update(VpnKeyModel)
                .where(VpnKeyModel.data_limit_bytes == NEW_LIMIT_BYTES)
                .values(data_limit_bytes=OLD_LIMIT_BYTES)
            )

            await session.commit()
            logger.info(f"✅ Rollback completado: {result.rowcount} llaves revertidas a 10GB")

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error durante el rollback: {e}")
            raise
        finally:
            await session.close()

    await engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrar límites de datos de llaves VPN de 10GB a 5GB"
    )
    parser.add_argument(
        "--rollback", action="store_true", help="Revertir la migración (5GB -> 10GB)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo mostrar cuántas llaves serían afectadas sin hacer cambios",
    )

    args = parser.parse_args()

    if args.rollback:
        asyncio.run(rollback_migration())
    elif args.dry_run:
        # Implementar dry-run
        async def dry_run():
            engine = create_async_engine(settings.DATABASE_URL)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with async_session() as session:
                result = await session.execute(
                    select(VpnKeyModel).where(VpnKeyModel.data_limit_bytes == OLD_LIMIT_BYTES)
                )
                keys = result.scalars().all()
                print(f"📊 DRY RUN: Se actualizarían {len(keys)} llaves de 10GB a 5GB")
                for key in keys[:10]:
                    print(f"   - ID: {key.id}, User: {key.user_id}, Name: {key.name}")
                if len(keys) > 10:
                    print(f"   ... y {len(keys) - 10} más")
                await session.close()
            await engine.dispose()

        asyncio.run(dry_run())
    else:
        asyncio.run(migrate_key_data_limits())
