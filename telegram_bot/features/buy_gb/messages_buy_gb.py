"""
Mensajes para el modulo de compra de GB.

Author: uSipipo Team
Version: 1.0.0
"""

from application.services.data_package_service import PACKAGE_OPTIONS


class BuyGbMessages:
    """Mensajes para compra de GB con Telegram Stars."""

    class Menu:
        PACKAGES_LIST = (
            "📦 **Paquetes de Datos Disponibles**\n\n"
            "{packages_list}\n"
            "⏱️ **Duracion:** 35 dias\n\n"
            "💡 *Selecciona un paquete para comprar*"
        )

        @staticmethod
        def format_packages_list() -> str:
            lines = []
            for pkg in PACKAGE_OPTIONS:
                bonus_text = f" (+{pkg.bonus_percent}% bonus)" if pkg.bonus_percent > 0 else ""
                lines.append(f"⭐ **{pkg.name}** - {pkg.data_gb} GB - {pkg.stars} ⭐{bonus_text}")
            return "\n".join(lines)

    class Payment:
        INVOICE_TITLE = "Paquete {package_name}"
        INVOICE_DESCRIPTION = "{gb_amount} GB de datos - Valido 35 dias"
        
        CONFIRMATION = (
            "✅ **Compra Exitosa**\n\n"
            "📦 **Paquete:** {package_name}\n"
            "📊 **Datos:** {gb_amount} GB{bonus_text}\n"
            "⭐ **Pagado:** {stars} estrellas\n"
            "📅 **Expira:** {expires_at}\n\n"
            "💎 *Tu paquete esta activo y listo para usar*"
        )

        PROCESSING = (
            "⏳ **Procesando Pago**\n\n"
            "Tu compra esta siendo procesada.\n\n"
            "💡 *Por favor espera un momento...*"
        )

    class Error:
        SYSTEM_ERROR = (
            "❌ **Error del Sistema**\n\n"
            "No pude procesar tu solicitud.\n\n"
            "Por favor, intenta mas tarde o contacta soporte."
        )

        PAYMENT_FAILED = (
            "❌ **Pago Fallido**\n\n"
            "No se pudo completar el pago.\n\n"
            "💡 *Por favor, intenta nuevamente*"
        )

        INVALID_PACKAGE = (
            "❌ **Paquete Invalido**\n\n"
            "El paquete seleccionado no es valido.\n\n"
            "💡 *Por favor, selecciona un paquete valido*"
        )

    class Info:
        DATA_SUMMARY = (
            "📊 **Resumen de Datos**\n\n"
            "📦 **Paquetes Activos:** {active_packages}\n"
            "📈 **Total Disponible:** {total_gb:.2f} GB\n"
            "📉 **Usado:** {used_gb:.2f} GB\n"
            "✅ **Restante:** {remaining_gb:.2f} GB\n\n"
            "💡 *Compra mas paquetes si necesitas mas datos*"
        )

    class Data:
        """Mensajes para comando /data."""

        HEADER = "💾 *Mis Datos*\n"

        DATA_INFO = (
            "📊 *Resumen de consumo:*\n\n"
            "📦 Paquetes activos: {active_packages}\n"
            "📥 Total disponible: {total_gb:.2f} GB\n"
            "📤 Datos usados: {used_gb:.2f} GB\n"
            "📥 Datos restantes: {remaining_gb:.2f} GB\n"
        )

        NO_DATA = (
            "💾 *Mis Datos*\n\n"
            "No tienes paquetes de datos activos.\n\n"
            "Usa /buy para adquirir más datos."
        )
