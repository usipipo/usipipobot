"""
Mensajes para el modulo de compra de GB.

Author: uSipipo Team
Version: 1.1.0
"""

from application.services.data_package_service import PACKAGE_OPTIONS, SLOT_OPTIONS


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
                bonus_text = (
                    f" (+{pkg.bonus_percent}% bonus)" if pkg.bonus_percent > 0 else ""
                )
                lines.append(
                    f"⭐ **{pkg.name}** - {pkg.data_gb} GB - {pkg.stars} ⭐{bonus_text}"
                )
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

        HEADER = "💾 *Tu Consumo de Datos*\n"
        SEPARATOR = "═══════════════════════\n"

        @staticmethod
        def format_packages_list(packages: list) -> str:
            if not packages:
                return ""
            lines = ["📦 *Paquetes Activos:*"]
            for pkg in packages:
                lines.append(
                    f"   • {pkg['name']} {pkg['total_gb']:.0f}GB ({pkg['days_remaining']} días restantes)"
                )
                lines.append(
                    f"     Usado: {pkg['used_gb']:.1f} GB / {pkg['total_gb']:.0f} GB"
                )
                lines.append(f"     Disponible: {pkg['remaining_gb']:.1f} GB")
            return "\n".join(lines)

        @staticmethod
        def format_free_plan(free_plan: dict) -> str:
            return (
                f"🎁 *Plan Free:*\n"
                f"   Disponible: {free_plan['remaining_gb']:.1f} GB"
            )

        @staticmethod
        def DATA_INFO(summary: dict) -> str:
            lines = [BuyGbMessages.Data.HEADER]
            lines.append("")
            lines.append(BuyGbMessages.Data.SEPARATOR)
            lines.append("")

            if summary.get("packages"):
                lines.append(
                    BuyGbMessages.Data.format_packages_list(summary["packages"])
                )
                lines.append("")
                lines.append(BuyGbMessages.Data.SEPARATOR)
                lines.append("")

            lines.append(BuyGbMessages.Data.format_free_plan(summary["free_plan"]))
            lines.append("")
            lines.append(BuyGbMessages.Data.SEPARATOR)
            lines.append("")
            lines.append(f"📊 *TOTAL DISPONIBLE:* {summary['remaining_gb']:.1f} GB")
            lines.append("")
            lines.append("💡 El consumo usa primero los paquetes comprados")

            return "\n".join(lines)

        NO_DATA = (
            "💾 *Mis Datos*\n\n"
            "No tienes paquetes de datos activos.\n\n"
            "Usa /buy para adquirir más datos."
        )

    class Slots:
        """Mensajes para compra de slots de claves."""

        MENU = (
            "🔑 **Slots de Claves Adicionales**\n\n"
            "Cada slot te permite crear una clave VPN adicional.\n\n"
            "{slots_list}\n\n"
            "💡 *Selecciona cuantas claves extra necesitas*"
        )

        @staticmethod
        def format_slots_list() -> str:
            lines = []
            for slot in SLOT_OPTIONS:
                lines.append(f"🔑 **{slot.name}** - {slot.stars} ⭐")
            return "\n".join(lines)

        INVOICE_TITLE = "Slots de Claves - {slots_name}"
        INVOICE_DESCRIPTION = "{slots} claves VPN adicionales"

        CONFIRMATION = (
            "✅ **Compra Exitosa**\n\n"
            "🔑 **Slots Adquiridos:** +{slots_added}\n"
            "📊 **Total de Claves:** {new_max_keys}\n"
            "⭐ **Pagado:** {stars} estrellas\n\n"
            "💎 *Ya puedes crear mas claves VPN*"
        )

        ERROR_MAX_KEYS = (
            "❌ **Limite Alcanzado**\n\n"
            "Ya tienes el maximo de claves permitidas.\n\n"
            "💡 *Contacta a soporte si necesitas mas*"
        )
