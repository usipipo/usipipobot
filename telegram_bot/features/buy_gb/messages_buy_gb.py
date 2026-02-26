"""
Mensajes para el modulo de compra de GB.

Author: uSipipo Team
Version: 1.1.0
"""

from datetime import datetime, timezone

from application.services.data_package_service import PACKAGE_OPTIONS, SLOT_OPTIONS


def _progress_bar(percentage: float, width: int = 10) -> str:
    """Genera barra de progreso ASCII estilo cyberpunk."""
    percentage = max(0, min(100, percentage))
    filled = int(width * percentage / 100)
    return "▓" * filled + "░" * (width - filled)


def _get_time_remaining(expires_at: datetime) -> tuple:
    """Calcula días y horas restantes hasta expiración."""
    if not expires_at:
        return 0, 0
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    delta = expires_at - now
    if delta.total_seconds() <= 0:
        return 0, 0
    days = delta.days
    hours = delta.seconds // 3600
    return days, hours


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

        SELECT_METHOD = (
            "💳 **Seleccionar Método de Pago**\n\n"
            "📦 **Paquete:** {package_name}\n"
            "📊 **Datos:** {gb_amount} GB\n\n"
            "⭐ **Precio con Stars:** {stars_price} ⭐\n"
            "💰 **Precio con Crypto:** {crypto_price:.2f} USDT\n\n"
            "💡 *Elige tu método de pago preferido*"
        )

        CRYPTO_INSTRUCTIONS = (
            "💰 **Pago con Cryptomoneda**\n\n"
            "📦 **Paquete:** {package_name}\n"
            "📊 **Datos:** {gb_amount} GB\n"
            "💰 **Monto a Pagar:** {usdt_amount:.2f} USDT\n\n"
            "🏦 **Enviar a esta dirección BSC:**\n"
            "`{wallet_address}`\n\n"
            "🔗 **Blockchain:** {blockchain}\n\n"
            "⚠️ **Importante:**\n"
            "• Solo envía **USDT** en la red **BSC**\n"
            "• El pago se procesa automáticamente\n"
            "• Recibirás confirmación cuando se complete\n\n"
            "💡 *Copia la dirección y realiza el pago*"
        )

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
        """Mensajes para comando /data - Estilo Cyberpunk Mobile-First."""

        HEADER = "💾 𝙳𝙰𝚃𝙰 𝙲𝙾𝙽𝚂𝚄𝙼𝙿𝚃𝙸𝙾𝙽"

        @staticmethod
        def format_packages_list(packages: list) -> str:
            if not packages:
                return ""
            lines = []
            for pkg in packages:
                percentage = (
                    (pkg["used_gb"] / pkg["total_gb"] * 100)
                    if pkg["total_gb"] > 0
                    else 0
                )
                progress = _progress_bar(percentage)
                days, hours = pkg.get("days_remaining", 0), pkg.get(
                    "hours_remaining", 0
                )

                lines.append(f"┌──────────────────────────┐")
                lines.append(f"│ 📦 {pkg['name'][:18]:<18} │")
                lines.append(f"├──────────────────────────┤")
                lines.append(
                    f"│ `{progress}` {percentage:.0f}%{' ' * (6 - len(f'{percentage:.0f}%'))}│"
                )
                gb_text = f"{pkg['used_gb']:.1f}/{pkg['total_gb']:.0f} GB"
                lines.append(f"│ ├ {gb_text}{' ' * (12 - len(gb_text))}│")
                lines.append(
                    f"│ └ ⏱️ {days}d {hours}h{' ' * (13 - len(f'{days}d {hours}h'))}│"
                )
                lines.append(f"└──────────────────────────┘")
                lines.append("")
            return "\n".join(lines)

        @staticmethod
        def format_free_plan(free_plan: dict) -> str:
            remaining = free_plan.get("remaining_gb", 0)
            limit = free_plan.get("limit_gb", 10)
            percentage = (remaining / limit * 100) if limit > 0 else 0
            progress = _progress_bar(percentage)

            return (
                f"┌──────────────────────────┐\n"
                f"│ 🎁 FREE TIER             │\n"
                f"├──────────────────────────┤\n"
                f"│ `{progress}` {percentage:.0f}%{' ' * (6 - len(f'{percentage:.0f}%'))}│\n"
                f"│ └ {remaining:.1f} GB{' ' * (16 - len(f'{remaining:.1f} GB'))}│\n"
                f"└──────────────────────────┘"
            )

        @staticmethod
        def DATA_INFO(summary: dict) -> str:
            lines = [BuyGbMessages.Data.HEADER]
            lines.append("")

            if summary.get("packages"):
                packages_with_time = []
                for pkg in summary["packages"]:
                    if "expires_at" in pkg and pkg["expires_at"]:
                        days, hours = _get_time_remaining(pkg["expires_at"])
                        pkg["days_remaining"] = days
                        pkg["hours_remaining"] = hours
                    else:
                        pkg["days_remaining"] = pkg.get("days_remaining", 0)
                        pkg["hours_remaining"] = pkg.get("hours_remaining", 0)
                    packages_with_time.append(pkg)

                lines.append(
                    BuyGbMessages.Data.format_packages_list(packages_with_time)
                )

            lines.append(BuyGbMessages.Data.format_free_plan(summary["free_plan"]))
            lines.append("")

            total_used = summary.get("total_used_gb", 0)
            total_limit = summary.get("total_limit_gb", 0)
            remaining = summary.get("remaining_gb", 0)

            lines.append(f"📊 *TOTAL:* `{remaining:.1f} GB`")
            lines.append("")
            lines.append("_💡 Packages → Free Tier_")

            return "\n".join(lines)

        NO_DATA = (
            "💾 *DATA CONSUMPTION*\n\n"
            "⚠️ No active packages\n\n"
            "Use `/buy` to acquire more data."
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
