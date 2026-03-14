import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from config import settings
from domain.entities.consumption_billing import BillingStatus
from domain.entities.consumption_invoice import ConsumptionInvoice, InvoiceStatus, PaymentMethod
from domain.interfaces.iconsumption_billing_repository import IConsumptionBillingRepository
from domain.interfaces.iconsumption_invoice_repository import IConsumptionInvoiceRepository
from domain.interfaces.iuser_repository import IUserRepository
from utils.logger import logger


@dataclass
class InvoiceGenerationResult:
    """DTO para resultado de generación de factura."""

    success: bool
    invoice: Optional[ConsumptionInvoice] = None
    error_message: Optional[str] = None
    wallet_address: Optional[str] = None  # Solo para pagos crypto


@dataclass
class PaymentResult:
    """DTO para resultado de procesamiento de pago."""

    success: bool
    invoice_id: Optional[uuid.UUID] = None
    error_message: Optional[str] = None


class ConsumptionInvoiceService:
    """
    Servicio de aplicación para gestionar facturas de consumo.

    Responsabilidades:
    - Generar facturas tras selección de método de pago
    - Verificar pagos en blockchain (crypto)
    - Procesar pagos exitosos
    - Cancelar facturas expiradas
    - Registrar transacciones en historial
    """

    def __init__(
        self,
        invoice_repo: IConsumptionInvoiceRepository,
        billing_repo: IConsumptionBillingRepository,
        user_repo: IUserRepository,
    ):
        self.invoice_repo = invoice_repo
        self.billing_repo = billing_repo
        self.user_repo = user_repo
        self.invoice_expiry_minutes = settings.CONSUMPTION_INVOICE_EXPIRY_MINUTES

    async def can_generate_invoice(
        self, user_id: int, current_user_id: int
    ) -> tuple[bool, Optional[str]]:
        """
        Verifica si un usuario puede generar una factura.

        Returns:
            Tuple de (puede_generar, mensaje_error)
        """
        # Verificar que el usuario tiene un ciclo cerrado (deuda)
        user = await self.user_repo.get_by_id(user_id, current_user_id)
        if not user:
            return False, "Usuario no encontrado"

        if not user.has_pending_debt:
            return False, "No tienes deudas pendientes"

        if not user.current_billing_id:
            return False, "No tienes un ciclo de facturación activo"

        # Verificar que el ciclo está cerrado (no pagado aún)
        billing = await self.billing_repo.get_by_id(user.current_billing_id, current_user_id)
        if not billing:
            return False, "Ciclo de facturación no encontrado"

        if billing.is_paid:
            return False, "Este ciclo ya está pagado"

        if billing.is_active:
            return False, "El ciclo de consumo aún está activo"

        # Verificar que no tiene una factura pendiente
        existing_invoice = await self.invoice_repo.get_pending_by_user(user_id, current_user_id)
        if existing_invoice and not existing_invoice.is_expired:
            return False, "Ya tienes una factura pendiente de pago"

        return True, None

    async def generate_invoice(
        self,
        user_id: int,
        payment_method: PaymentMethod,
        wallet_address: Optional[str],
        current_user_id: int,
    ) -> InvoiceGenerationResult:
        """
        Genera una factura tras selección del método de pago.

        Args:
            user_id: ID del usuario
            payment_method: Método de pago seleccionado (STARS o CRYPTO)
            wallet_address: Dirección de wallet (requerido para crypto)
            current_user_id: ID del usuario actual (para auditoría)

        Returns:
            InvoiceGenerationResult con la factura generada o error
        """
        logger.info(f"🧾 Generando factura - user_id={user_id}, " f"method={payment_method.value}")

        try:
            # Validar que puede generar factura
            can_generate, error_msg = await self.can_generate_invoice(user_id, current_user_id)
            if not can_generate:
                logger.warning(f"⚠️ No se puede generar factura: {error_msg}")
                return InvoiceGenerationResult(success=False, error_message=error_msg)

            # Obtener el ciclo de facturación
            user = await self.user_repo.get_by_id(user_id, current_user_id)
            if not user or user.current_billing_id is None:
                return InvoiceGenerationResult(
                    success=False,
                    error_message="No se encontró el ciclo de facturación",
                )

            billing = await self.billing_repo.get_by_id(user.current_billing_id, current_user_id)
            if not billing or billing.id is None:
                return InvoiceGenerationResult(
                    success=False, error_message="Ciclo de facturación no válido"
                )

            # Validar método de pago y datos requeridos
            if payment_method == PaymentMethod.CRYPTO and not wallet_address:
                return InvoiceGenerationResult(
                    success=False,
                    error_message="Se requiere dirección de wallet para pago con crypto",
                )

            # Para pagos con Stars, no necesitamos wallet
            if payment_method == PaymentMethod.STARS:
                wallet_address = "N/A"

            # Crear factura
            invoice = ConsumptionInvoice(
                billing_id=billing.id,
                user_id=user_id,
                amount_usd=billing.total_cost_usd,
                wallet_address=wallet_address or "N/A",
                payment_method=payment_method,
                status=InvoiceStatus.PENDING,
            )

            # Ajustar tiempo de expiración según configuración
            from datetime import timedelta

            invoice.expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=self.invoice_expiry_minutes
            )

            saved_invoice = await self.invoice_repo.save(invoice, current_user_id)

            logger.info(
                f"✅ Factura generada - invoice_id={saved_invoice.id}, "
                f"amount=${saved_invoice.amount_usd:.2f}, "
                f"method={payment_method.value}"
            )

            return InvoiceGenerationResult(
                success=True,
                invoice=saved_invoice,
                wallet_address=(wallet_address if payment_method == PaymentMethod.CRYPTO else None),
            )

        except Exception as e:
            logger.error(f"❌ Error generando factura: {e}")
            return InvoiceGenerationResult(
                success=False, error_message="Error interno al generar la factura"
            )

    async def process_crypto_payment(
        self, invoice_id: uuid.UUID, transaction_hash: str, current_user_id: int
    ) -> PaymentResult:
        """
        Procesa un pago con crypto exitoso.

        Args:
            invoice_id: ID de la factura
            transaction_hash: Hash de la transacción blockchain
            current_user_id: ID del usuario actual (para auditoría)

        Returns:
            PaymentResult con éxito o error
        """
        try:
            invoice = await self.invoice_repo.get_by_id(invoice_id, current_user_id)
            if not invoice:
                return PaymentResult(success=False, error_message="Factura no encontrada")

            if invoice.payment_method != PaymentMethod.CRYPTO:
                return PaymentResult(
                    success=False,
                    error_message="Esta factura no es para pago con crypto",
                )

            # Verificar que la factura no haya expirado
            if invoice.is_expired:
                await self.invoice_repo.mark_as_expired(invoice_id, current_user_id)
                return PaymentResult(
                    success=False,
                    error_message="La factura ha expirado. Genera una nueva.",
                )

            # Marcar como pagada
            success = await self.invoice_repo.mark_as_paid(
                invoice_id, transaction_hash, current_user_id
            )

            if success:
                # Actualizar ciclo de facturación
                await self.billing_repo.update_status(
                    invoice.billing_id, BillingStatus.PAID, current_user_id
                )

                # Actualizar usuario (limpiar deuda, desactivar modo consumo)
                user = await self.user_repo.get_by_id(invoice.user_id, current_user_id)
                if user:
                    user.mark_debt_as_paid()
                    user.deactivate_consumption_mode()
                    await self.user_repo.save(user, current_user_id)

                    # Unblock all user keys
                    from application.services.common.container import get_container
                    from application.services.consumption_vpn_integration_service import (
                        ConsumptionVpnIntegrationService,
                    )

                    container = get_container()
                    vpn_integration = container.resolve(ConsumptionVpnIntegrationService)
                    unblock_result = await vpn_integration.unblock_user_keys(
                        user.telegram_id, current_user_id
                    )

                    if not unblock_result["success"]:
                        logger.error(
                            f"Failed to unblock keys for user {user.telegram_id}: "
                            f"{unblock_result['errors']}"
                        )

                # Registrar en historial de transacciones
                await self._record_transaction(invoice, current_user_id)

                logger.info(
                    f"💰 Pago crypto procesado - invoice_id={invoice_id}, "
                    f"tx_hash={transaction_hash[:10]}..., "
                    f"amount=${invoice.amount_usd:.2f}"
                )

                return PaymentResult(success=True, invoice_id=invoice_id)

            return PaymentResult(success=False, error_message="No se pudo procesar el pago")

        except Exception as e:
            logger.error(f"❌ Error procesando pago crypto: {e}")
            return PaymentResult(success=False, error_message="Error interno")

    async def process_stars_payment(
        self, invoice_id: uuid.UUID, telegram_payment_id: str, current_user_id: int
    ) -> PaymentResult:
        """
        Procesa un pago con Telegram Stars exitoso.

        Args:
            invoice_id: ID de la factura
            telegram_payment_id: ID del pago de Telegram
            current_user_id: ID del usuario actual (para auditoría)

        Returns:
            PaymentResult con éxito o error
        """
        try:
            invoice = await self.invoice_repo.get_by_id(invoice_id, current_user_id)
            if not invoice:
                return PaymentResult(success=False, error_message="Factura no encontrada")

            if invoice.payment_method != PaymentMethod.STARS:
                return PaymentResult(
                    success=False,
                    error_message="Esta factura no es para pago con Stars",
                )

            # Verificar que la factura no haya expirado
            if invoice.is_expired:
                await self.invoice_repo.mark_as_expired(invoice_id, current_user_id)
                return PaymentResult(
                    success=False,
                    error_message="La factura ha expirado. Genera una nueva.",
                )

            # Marcar como pagada
            invoice.mark_as_paid(telegram_payment_id=telegram_payment_id)
            success = await self.invoice_repo.save(invoice, current_user_id)

            if success:
                # Actualizar ciclo de facturación
                await self.billing_repo.update_status(
                    invoice.billing_id, BillingStatus.PAID, current_user_id
                )

                # Actualizar usuario (limpiar deuda, desactivar modo consumo)
                user = await self.user_repo.get_by_id(invoice.user_id, current_user_id)
                if user:
                    user.mark_debt_as_paid()
                    user.deactivate_consumption_mode()
                    await self.user_repo.save(user, current_user_id)

                    # Unblock all user keys
                    from application.services.common.container import get_container
                    from application.services.consumption_vpn_integration_service import (
                        ConsumptionVpnIntegrationService,
                    )

                    container = get_container()
                    vpn_integration = container.resolve(ConsumptionVpnIntegrationService)
                    unblock_result = await vpn_integration.unblock_user_keys(
                        user.telegram_id, current_user_id
                    )

                    if not unblock_result["success"]:
                        logger.error(
                            f"Failed to unblock keys for user {user.telegram_id}: "
                            f"{unblock_result['errors']}"
                        )

                # Registrar en historial de transacciones
                await self._record_transaction(invoice, current_user_id)

                logger.info(
                    f"⭐ Pago Stars procesado - invoice_id={invoice_id}, "
                    f"payment_id={telegram_payment_id[:10]}..., "
                    f"amount=${invoice.amount_usd:.2f}"
                )

                return PaymentResult(success=True, invoice_id=invoice_id)

            return PaymentResult(success=False, error_message="No se pudo procesar el pago")

        except Exception as e:
            logger.error(f"❌ Error procesando pago Stars: {e}")
            return PaymentResult(success=False, error_message="Error interno")

    async def _record_transaction(self, invoice: ConsumptionInvoice, current_user_id: int) -> None:
        """
        Registra la transacción en el historial del usuario.
        Este método integra con el sistema de transacciones existente.
        """
        try:
            # Aquí se integraría con el TransactionRepository existente
            # Por ahora solo logueamos
            logger.info(
                f"📝 Transacción registrada - user_id={invoice.user_id}, "
                f"amount=${invoice.amount_usd:.2f}, "
                f"method={invoice.payment_method.value}, "
                f"billing_id={invoice.billing_id}"
            )
        except Exception as e:
            logger.error(f"❌ Error registrando transacción: {e}")

    async def cancel_expired_invoices(self, current_user_id: int) -> int:
        """
        Cancela facturas que han expirado.

        Returns:
            Cantidad de facturas canceladas
        """
        try:
            expired_invoices = await self.invoice_repo.get_expired_pending(current_user_id)

            count = 0
            for invoice in expired_invoices:
                if invoice.id and await self.invoice_repo.mark_as_expired(
                    invoice.id, current_user_id
                ):
                    count += 1

            if count > 0:
                logger.info(f"🗑️ {count} facturas expiradas canceladas")

            return count

        except Exception as e:
            logger.error(f"❌ Error cancelando facturas expiradas: {e}")
            return 0

    async def get_pending_invoice(
        self, user_id: int, current_user_id: int
    ) -> Optional[ConsumptionInvoice]:
        """
        Obtiene la factura pendiente de un usuario.

        Args:
            user_id: ID del usuario
            current_user_id: ID del usuario actual (para auditoría)

        Returns:
            ConsumptionInvoice o None si no tiene factura pendiente
        """
        invoice = await self.invoice_repo.get_pending_by_user(user_id, current_user_id)

        # Verificar si ha expirado
        if invoice and invoice.is_expired and invoice.id:
            await self.invoice_repo.mark_as_expired(invoice.id, current_user_id)
            return None

        return invoice

    async def get_invoice_by_id(
        self, invoice_id: uuid.UUID, current_user_id: int
    ) -> Optional[ConsumptionInvoice]:
        """
        Obtiene una factura por su ID.

        Args:
            invoice_id: ID de la factura
            current_user_id: ID del usuario actual (para auditoría)

        Returns:
            ConsumptionInvoice o None si no existe
        """
        return await self.invoice_repo.get_by_id(invoice_id, current_user_id)
