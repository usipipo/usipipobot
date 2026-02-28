"""
Mensajes para el módulo de tarifa por consumo (Pay-as-You-Go).

Author: uSipipo Team
Version: 1.0.0
"""


class ConsumptionMessages:
    """Mensajes para el sistema de tarifa por consumo."""

    class Activation:
        """Mensajes relacionados con la activación del modo consumo."""

        WARNING_HEADER = (
            "⚠️ **¡ATENCIÓN: MODO CONSUMO LIBRE!** ⚠️\n\n"
            "Estás a punto de activar la **Tarifa por Consumo**. "
            "Lee cuidadosamente los términos antes de continuar.\n"
        )

        TERMS_AND_CONDITIONS = (
            "📋 **TÉRMINOS Y CONDICIONES**\n\n"
            "1️⃣ **Consumo Ilimitado:**\n"
            "   • Navegarás sin límites de velocidad ni de datos\n"
            "   • Los 5GB gratuitos mensuales se pausan temporalmente\n\n"
            "2️⃣ **Facturación Postpago:**\n"
            "   • En **30 días** recibirás una factura por el consumo total\n"
            "   • Precio: **$0.45 USD por GB** (10% más barato que plan estándar)\n"
            "   • Pagas exactamente lo que consumes, al centavo\n\n"
            "3️⃣ **Consecuencias de No Pagar:**\n"
            "   • Si no pagas la factura, **TODAS tus claves VPN serán bloqueadas**\n"
            "   • Incluye las claves con datos gratuitos\n"
            "   • No podrás usar el servicio hasta pagar la deuda\n\n"
            "4️⃣ **Desactivación Automática:**\n"
            "   • Al pagar, el modo consumo se desactiva automáticamente\n"
            "   • Debes reactivarlo manualmente si deseas otro ciclo\n\n"
            "⚠️ **Este es un sistema de crédito basado en confianza.**\n"
            "Al activar este modo, asumes toda la responsabilidad del consumo."
        )

        PRICE_EXAMPLE = (
            "💰 **EJEMPLO DE COSTOS**\n\n"
            "Si consumes:\n"
            "• 1 GB = $0.45 USD\n"
            "• 5 GB = $2.25 USD\n"
            "• 10 GB = $4.50 USD (vs $5.00 en plan estándar)\n\n"
            "💡 *Si usas menos de 10GB, pagas menos. Si usas más, sigues pagando "
            "solo $0.45/GB sin límites.*"
        )

        CONFIRMATION_PROMPT = (
            "❓ **¿Aceptas activar la tarifa por consumo bajo tu propia "
            "responsabilidad?**\n\n"
            "Al presionar '✅ Acepto', confirmas que:\n"
            "• Entiendes que pagarás postconsumo\n"
            "• Aceptas que tus claves se bloquearán si no pagas\n"
            "• Has leído y comprendido todos los términos"
        )

        SUCCESS = (
            "✅ **¡Modo Consumo Activado!**\n\n"
            "🚀 Ahora puedes navegar **sin límites**\n"
            "📅 Tu ciclo de 30 días comenzó hoy\n"
            "💰 Pagas solo por lo que consumes: $0.45/GB\n\n"
            "📊 Usa `/mi_consumo` para ver tu consumo actual\n"
            "ℹ️ En 30 días recibirás tu factura"
        )

        ALREADY_ACTIVE = (
            "ℹ️ **Ya tienes el modo consumo activo**\n\n"
            "📊 Usa `/mi_consumo` para ver tu consumo actual\n"
            "📅 Tu ciclo cierra en {days_remaining} días"
        )

        CANNOT_ACTIVATE = (
            "❌ **No puedes activar el modo consumo**\n\n"
            "{reason}\n\n"
            "💡 Resuelve este problema antes de intentar nuevamente."
        )

    class ConsumptionStatus:
        """Mensajes para consulta de consumo."""

        ACTIVE_CYCLE = (
            "📊 **Tu Consumo Actual**\n\n"
            "🔄 **Estado:** Activo (consumiendo)\n"
            "📅 **Días activo:** {days_active}/30\n"
            "📈 **Consumo:** {consumption_formatted}\n"
            "💰 **Costo acumulado:** {cost_formatted}\n\n"
            "💡 *El ciclo cierra en {days_remaining} días. "
            "Recuerda que pagarás por lo consumido.*"
        )

        CLOSED_CYCLE = (
            "🔒 **Ciclo Cerrado - Deuda Pendiente**\n\n"
            "📅 **Días totales:** 30/30\n"
            "📈 **Consumo total:** {consumption_formatted}\n"
            "💰 **Total a pagar:** {cost_formatted}\n\n"
            "⚠️ **Tus claves VPN están bloqueadas**\n\n"
            "💳 Presiona 'Generar Factura' para pagar y desbloquear"
        )

        NO_ACTIVE_CYCLE = (
            "ℹ️ **No tienes modo consumo activo**\n\n"
            "📦 Tu plan actual:\n"
            "• 5GB gratuitos mensuales por clave\n\n"
            "💡 ¿Quieres navegar sin límites?\n"
            "Activa la Tarifa por Consumo en el menú principal."
        )

    class Invoice:
        """Mensajes para facturación y pagos."""

        SELECT_PAYMENT_METHOD = (
            "💳 **Selecciona Método de Pago**\n\n"
            "📈 **Consumo total:** {consumption_formatted}\n"
            "💰 **Total a pagar:** {cost_formatted}\n\n"
            "¿Cómo deseas pagar?"
        )

        CRYPTO_PAYMENT = (
            "💰 **Pago con USDT - BSC**\n\n"
            "📈 **Consumo:** {consumption_formatted}\n"
            "💰 **Monto a pagar:** {cost_formatted}\n\n"
            "📋 **Wallet para pago:**\n"
            "`{wallet_address}`\n\n"
            "⏱️ **Tiempo límite:** {time_remaining}\n\n"
            "⚠️ **Importante:**\n"
            "• Envía exactamente el monto indicado\n"
            "• Solo USDT en red BSC (BEP20)\n"
            "• Espera las confirmaciones de la red\n\n"
            "✅ El sistema detectará automáticamente tu pago"
        )

        STARS_PAYMENT = (
            "💫 **Pago con Telegram Stars**\n\n"
            "📈 **Consumo:** {consumption_formatted}\n"
            "💰 **Equivalente:** {cost_formatted}\n"
            "⭐ **Stars a pagar:** {stars_amount} ⭐\n\n"
            "⏱️ **Tiempo límite:** {time_remaining}\n\n"
            "✅ Presiona el botón de pago para completar la transacción"
        )

        PAYMENT_SUCCESS = (
            "🎉 **¡Pago Recibido Exitosamente!**\n\n"
            "💰 **Monto pagado:** {cost_formatted}\n"
            "📈 **Consumo pagado:** {consumption_formatted}\n\n"
            "✅ Tu deuda ha sido liquidada\n"
            "🔓 Todas tus claves VPN han sido desbloqueadas\n"
            "📦 Los 5GB gratuitos mensuales han sido reactivados\n\n"
            "⚠️ **El modo consumo se ha desactivado automáticamente.**\n"
            "Si deseas volver a navegar sin límites, actívalo nuevamente."
        )

        PAYMENT_EXPIRED = (
            "⏱️ **Factura Expirada**\n\n"
            "La factura generada ha expirado (30 minutos).\n\n"
            "💡 Genera una nueva factura para realizar el pago."
        )

        NO_PENDING_DEBT = (
            "ℹ️ **No tienes deudas pendientes**\n\n"
            "✅ Estás al día con tus pagos"
        )

    class Menu:
        """Mensajes del menú principal de consumo."""

        MAIN_MENU = (
            "⚡ **Tarifa por Consumo**\n\n"
            "📊 **Tu estado:**\n"
            "{status_text}\n\n"
            "💡 *Navega sin límites y paga solo por lo que consumes*"
        )

        STATUS_ACTIVE = (
            "✅ Modo consumo ACTIVO\n"
            "📊 Usa `/mi_consumo` para ver detalles"
        )

        STATUS_INACTIVE = (
            "⭕ Modo consumo INACTIVO\n"
            "📦 Usando plan gratuito (5GB/clave)"
        )

        STATUS_DEBT = (
            "🔴 TIENES DEUDA PENDIENTE\n"
            "💳 Genera factura para pagar"
        )

    class Error:
        """Mensajes de error."""

        GENERIC = (
            "❌ **Error del sistema**\n\n"
            "Ocurrió un error inesperado. Por favor, intenta nuevamente."
        )

        INVOICE_GENERATION = (
            "❌ **Error generando factura**\n\n"
            "{reason}\n\n"
            "💡 Intenta nuevamente o contacta al soporte."
        )

        PAYMENT_PROCESSING = (
            "❌ **Error procesando pago**\n\n"
            "{reason}\n\n"
            "💡 Si el problema persiste, contacta al soporte."
        )

    class Cron:
        """Mensajes para notificaciones del cron job."""

        CYCLE_CLOSED = (
            "🔔 **Tu ciclo de consumo ha cerrado**\n\n"
            "📅 Se completaron los 30 días de consumo\n"
            "📈 **Consumo total:** {consumption_formatted}\n"
            "💰 **Total a pagar:** {cost_formatted}\n\n"
            "🔒 **Tus claves VPN han sido bloqueadas**\n\n"
            "💳 Genera tu factura y paga para desbloquear el servicio"
        )
