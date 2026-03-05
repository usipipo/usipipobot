#!/usr/bin/env python3
"""
Script de cron job para cerrar ciclos de consumo expirados.

Este script se ejecuta diariamente y:
1. Busca ciclos de consumo activos que han excedido 30 días
2. Cierra los ciclos y marca deuda al usuario
3. Bloquea las claves VPN de usuarios con deuda
4. Envía notificaciones a los usuarios afectados

Uso:
    python scripts/run_consumption_cron.py

Configuración cron (cada día a las 00:00 UTC):
    0 0 * * * cd /path/to/bot && venv/bin/python \
        scripts/run_consumption_cron.py >> logs/cron.log 2>&1
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# flake8: noqa: E402
from application.services.consumption_billing_service import (
    ConsumptionBillingService,
)
from application.services.consumption_invoice_service import (
    ConsumptionInvoiceService,
)
from config import settings
from infrastructure.persistence.database import get_session_context
from infrastructure.persistence.postgresql.consumption_billing_repository import (
    PostgresConsumptionBillingRepository,
)
from infrastructure.persistence.postgresql.consumption_invoice_repository import (
    PostgresConsumptionInvoiceRepository,
)
from infrastructure.persistence.postgresql.user_repository import (
    PostgresUserRepository,
)
from utils.logger import logger


class ConsumptionCronJob:
    """Cron job para gestionar ciclos de consumo expirados."""

    def __init__(self):
        self.admin_id = settings.ADMIN_ID
        self.cycle_days = settings.CONSUMPTION_CYCLE_DAYS

    async def run(self) -> dict:
        """
        Ejecuta el cron job.

        Returns:
            Dict con estadísticas de la ejecución
        """
        stats = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "cycles_closed": 0,
            "users_notified": 0,
            "errors": 0,
        }

        async with get_session_context() as session:
            # Inicializar repositorios
            billing_repo = PostgresConsumptionBillingRepository(session)
            invoice_repo = PostgresConsumptionInvoiceRepository(session)
            user_repo = PostgresUserRepository(session)

            # Inicializar servicios
            billing_service = ConsumptionBillingService(billing_repo, user_repo)
            invoice_service = ConsumptionInvoiceService(
                invoice_repo, billing_repo, user_repo
            )

            try:
                logger.info("🔄 Iniciando cron job de consumo...")

                # 1. Obtener ciclos expirados
                expired_cycles = await billing_service.get_expired_cycles(self.admin_id)

                logger.info(f"📊 Ciclos expirados encontrados: {len(expired_cycles)}")

                # 2. Procesar cada ciclo expirado
                for cycle in expired_cycles:
                    try:
                        if not cycle.id:
                            continue

                        success = await billing_service.close_billing_cycle(
                            cycle.id, self.admin_id
                        )

                        if success:
                            stats["cycles_closed"] += 1
                            stats["users_notified"] += 1

                            logger.info(
                                f"🔒 Ciclo cerrado - user_id={cycle.user_id}, "
                                f"billing_id={cycle.id}, "
                                f"cost=${cycle.total_cost_usd:.2f}"
                            )

                            # Aquí se enviaría notificación al usuario
                            # (requiere integración con bot de Telegram)
                            await self._notify_user(cycle)

                    except Exception as e:
                        stats["errors"] += 1
                        logger.error(f"❌ Error procesando ciclo {cycle.id}: {e}")

                # 3. Cancelar facturas expiradas
                expired_invoices = await invoice_service.cancel_expired_invoices(
                    self.admin_id
                )

                if expired_invoices > 0:
                    logger.info(f"🗑️ Facturas expiradas canceladas: {expired_invoices}")

                stats["finished_at"] = datetime.now(timezone.utc).isoformat()

                logger.info(
                    f"✅ Cron job completado - "
                    f"ciclos_cerrados={stats['cycles_closed']}, "
                    f"errores={stats['errors']}"
                )

            except Exception as e:
                stats["errors"] += 1
                logger.error(f"❌ Error en cron job: {e}")

        return stats

    async def _notify_user(self, cycle) -> None:
        """
        Notifica al usuario que su ciclo ha cerrado.

        Nota: Esta es una implementación placeholder. En producción,
        se integraría con el bot de Telegram para enviar mensajes.
        """
        try:
            # Formato del mensaje (sin enviar realmente)
            consumption_str = cycle.get_formatted_consumption()
            cost_str = cycle.get_formatted_cost()

            logger.info(
                f"📨 Notificación preparada para user_id={cycle.user_id}: "
                f"Consumo={consumption_str}, Costo={cost_str}"
            )

            # Aquí se enviaría el mensaje real usando el bot
            # from telegram import Bot
            # bot = Bot(token=settings.TELEGRAM_TOKEN)
            # await bot.send_message(chat_id=cycle.user_id, text=message)

        except Exception as e:
            logger.error(f"❌ Error notificando a usuario {cycle.user_id}: {e}")


async def main():
    """Punto de entrada principal."""
    logger.info("=" * 50)
    logger.info("🚀 Iniciando Consumption Cron Job")
    logger.info(f"⏰ Hora UTC: {datetime.now(timezone.utc).isoformat()}")
    logger.info(f"📅 Días de ciclo: {settings.CONSUMPTION_CYCLE_DAYS}")
    logger.info("=" * 50)

    job = ConsumptionCronJob()
    stats = await job.run()

    # Imprimir estadísticas
    print("\n" + "=" * 50)
    print("📊 ESTADÍSTICAS DEL CRON JOB")
    print("=" * 50)
    print(f"Inicio: {stats['started_at']}")
    print(f"Ciclos cerrados: {stats['cycles_closed']}")
    print(f"Usuarios notificados: {stats['users_notified']}")
    print(f"Errores: {stats['errors']}")
    print(f"Fin: {stats['finished_at']}")
    print("=" * 50)

    # Retornar código de salida
    return 0 if stats["errors"] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
