"""
Mensajes para operaciones del usuario de uSipipo.

Author: uSipipo Team
Version: 2.0.0 - Feature-based architecture
"""


class OperationsMessages:
    """Mensajes para operaciones del usuario."""

    # ============================================
    # MENU
    # ============================================

    class Menu:
        """Mensajes del menú de operaciones."""

        MAIN = (
            "💰 **Centro de Operaciones**\n\n"
            "Gestiona tu cuenta y accede a servicios:\n\n"
            "💎 **Balance y Transacciones**\n"
            "👥 **Sistema de Referidos**\n"
            "🎮 **Juegos y Recompensas**\n\n"
            "Selecciona una opción:"
        )

    # ============================================
    # BALANCE
    # ============================================

    class Balance:
        """Mensajes de balance."""

        DISPLAY = (
            "💰 **Tu Balance**\n\n"
            "👤 **Usuario:** {name}\n"
            "⭐ **Balance Actual:** {balance} estrellas\n"
            "💳 **Total Depositado:** ${total_deposited:.2f}\n"
            "💸 **Total Gastado:** ${total_spent:.2f}\n"
            "🎁 **Ganancias Referidos:** {referral_earnings} estrellas\n\n"
            "💡 Usa tus estrellas para desbloquear contenido premium."
        )

        NO_BALANCE = (
            "💰 **Sin Balance**\n\n"
            "No tienes estrellas en tu cuenta.\n\n"
            "💡 *Opciones para obtener estrellas:*\n"
            "• Deposita fondos\n"
            "• Invita amigos (referidos)\n"
            "• Completa logros y juegos"
        )

        TRANSACTION_SUCCESS = (
            "✅ **Transacción Exitosa**\n\n"
            "Tu balance ha sido actualizado.\n\n"
            "💰 **Nuevo Balance:** {balance} estrellas"
        )

        TRANSACTION_FAILED = (
            "❌ **Transacción Fallida**\n\n"
            "No pude procesar tu transacción.\n\n"
            "Error: {error}"
        )

    # ============================================
    # TRANSACTIONS
    # ============================================

    class Transactions:
        """Mensajes de transacciones."""

        HISTORY = (
            "📊 **Historial de Transacciones**\n\n"
            "Usuario: {user_id}\n"
            "Total de transacciones: {count}\n\n"
            "📋 *Aquí se mostrará tu historial completo*"
        )

        TRANSACTION_DETAIL = (
            "📋 **Detalle de Transacción**\n\n"
            "🆔 **ID:** {transaction_id}\n"
            "📅 **Fecha:** {date}\n"
            "💰 **Monto:** ${amount:.2f}\n"
            "📝 **Descripción:** {description}\n"
            "🟢 **Estado:** {status}\n\n"
            "💡 *Esta transacción ya ha sido procesada*"
        )

        NO_TRANSACTIONS = (
            "📭 **Sin Transacciones**\n\n"
            "No tienes transacciones registradas.\n\n"
            "💡 *Realiza tu primera operación para ver el historial*"
        )

    # ============================================
    # ERRORS
    # ============================================

    class Error:
        """Mensajes de error."""

        SYSTEM_ERROR = (
            "❌ **Error del Sistema**\n\n"
            "No pude procesar tu solicitud.\n\n"
            "Por favor, intenta más tarde."
        )

        SERVICE_UNAVAILABLE = (
            "⚠️ **Servicio No Disponible**\n\n"
            "Esta función no está disponible temporalmente.\n\n"
            "Por favor, intenta más tarde."
        )

        INSUFFICIENT_BALANCE = (
            "💸 **Balance Insuficiente**\n\n"
            "No tienes suficientes estrellas para esta operación.\n\n"
            "💡 *Recarga tu balance para continuar*"
        )

        INVALID_AMOUNT = (
            "❌ **Monto Inválido**\n\n"
            "El monto especificado no es válido.\n\n"
            "💡 *Verifica el amounto e intenta nuevamente*"
        )

    # ============================================
    # SUCCESS
    # ============================================

    class Success:
        """Mensajes de éxito."""

        OPERATION_COMPLETED = (
            "✅ **Operación Completada**\n\n"
            "Tu solicitud ha sido procesada exitosamente."
        )

        PAYMENT_PROCESSED = (
            "💳 **Pago Procesado**\n\n"
            "Tu pago ha sido procesado correctamente.\n\n"
            "💰 **Balance Actualizado:** {balance} estrellas"
        )

        REFERRAL_LINK_SHARED = (
            "🔗 **Enlace Compartido**\n\n"
            "Tu enlace de referido está listo para compartir.\n\n"
            "💡 *Cuanta más gente invites, más ganas!*"
        )
