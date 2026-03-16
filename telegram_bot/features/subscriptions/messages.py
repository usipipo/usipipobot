"""
Mensajes para gestión de suscripciones de uSipipo.

Author: uSipipo Team
Version: 1.0.0
"""

from utils.message_separators import TELEGRAM_MOBILE_WIDTH, MessageSeparatorBuilder

# Separadores predefinidos para consistencia visual
_SEP_HEADER = (
    MessageSeparatorBuilder().compact().style("double").length(TELEGRAM_MOBILE_WIDTH).build()
)
_SEP_DIVIDER = (
    MessageSeparatorBuilder().compact().style("simple").length(TELEGRAM_MOBILE_WIDTH).build()
)


class SubscriptionMessages:
    """Mensajes para gestión de suscripciones."""

    class Menu:
        """Mensajes para el menú de suscripciones."""

        _HEADER = f"{_SEP_HEADER}\n" "💎 *PLANES PREMIUM*\n" f"{_SEP_HEADER}\n"

        _PREMIUM_STATUS = (
            "\n" "👑 *Estado Premium:* `{status}`\n" "📊 *Datos:* {data_info}\n" f"{_SEP_DIVIDER}\n"
        )

        _PLAN_LIST = (
            "\n"
            "*Planes disponibles:*\n"
            "│\n"
            "├─ 🥇 *1 Mes*\n"
            "│  └─ 360 Stars | Datos Ilimitados\n"
            "│\n"
            "├─ 🥈 *3 Meses*\n"
            "│  └─ 960 Stars | Datos Ilimitados (+11% bonus)\n"
            "│\n"
            "└─ 🥉 *6 Meses*\n"
            "   └─ 1560 Stars | Datos Ilimitados (+13% bonus)\n"
        )

        _FOOTER = f"\n{_SEP_DIVIDER}\n" "👇 *Selecciona un plan:*\n"

        @classmethod
        def menu(cls, is_premium: bool = False, days_remaining: int = 0) -> str:
            """Generate subscription menu message."""
            message = cls._HEADER

            if is_premium:
                status = "ACTIVO"
                data_info = f"Ilimitados ({days_remaining} días restantes)"
            else:
                status = "INACTIVO"
                data_info = "10 GB (Plan Básico)"

            message += cls._PREMIUM_STATUS.format(status=status, data_info=data_info)
            message += cls._PLAN_LIST
            message += cls._FOOTER

            return message

        # Legacy fallback (without dynamic data)
        MAIN = (
            _HEADER
            + _PREMIUM_STATUS.format(status="INACTIVO", data_info="10 GB (Plan Básico)")
            + _PLAN_LIST
            + _FOOTER
        )

    class SubscriptionInfo:
        """Mensajes para información de suscripción activa."""

        _HEADER = f"{_SEP_HEADER}\n" "👑 *TU SUSCRIPCIÓN PREMIUM*\n" f"{_SEP_HEADER}\n"

        _INFO_BODY = (
            "\n"
            "*Plan:* {plan_name}\n"
            "*Estado:* ✅ Activo\n"
            "*Datos:* 🌐 Ilimitados\n"
            "*Vence:* {expires_at}\n"
            "*Días restantes:* {days_remaining}\n"
            f"{_SEP_DIVIDER}\n"
        )

        _BENEFITS = (
            "\n"
            "*Beneficios incluidos:*\n"
            "│\n"
            "├─ 🌐 Datos ilimitados en VPN\n"
            "├─ ⚡ Velocidad prioritaria\n"
            "├─ 🎯 Soporte prioritario\n"
            "└─ 🔒 Sin límites de consumo\n"
        )

        _FOOTER = f"\n{_SEP_DIVIDER}\n" "👇 *Gestiona tu suscripción:*\n"

        @classmethod
        def active_subscription(cls, plan_name: str, expires_at: str, days_remaining: int) -> str:
            """Generate active subscription info message."""
            message = cls._HEADER
            message += cls._INFO_BODY.format(
                plan_name=plan_name,
                expires_at=expires_at,
                days_remaining=days_remaining,
            )
            message += cls._BENEFITS
            message += cls._FOOTER
            return message

    class PurchaseConfirmation:
        """Mensajes para confirmación de compra."""

        _HEADER = f"{_SEP_HEADER}\n" "🛒 *CONFIRMACIÓN DE COMPRA*\n" f"{_SEP_HEADER}\n"

        _CONFIRMATION_BODY = (
            "\n"
            "*Plan:* {plan_name}\n"
            "*Precio:* {stars} Stars ⭐\n"
            "*Duración:* {duration} días\n"
            "*Datos:* 🌐 Ilimitados\n"
            f"{_SEP_DIVIDER}\n"
            "¿Confirmar compra?\n"
        )

        @classmethod
        def confirm_purchase(cls, plan_name: str, stars: int, duration: int) -> str:
            """Generate purchase confirmation message."""
            message = cls._HEADER
            message += cls._CONFIRMATION_BODY.format(
                plan_name=plan_name,
                stars=stars,
                duration=duration,
            )
            return message

    class Success:
        """Mensajes de éxito."""

        _HEADER = f"{_SEP_HEADER}\n" "✅ *¡SUSCRIPCIÓN ACTIVADA!*\n" f"{_SEP_HEADER}\n"

        _SUCCESS_BODY = (
            "\n"
            "🎉 ¡Felicidades! Ahora eres usuario Premium\n"
            "\n"
            "*Plan:* {plan_name}\n"
            "*Stars gastados:* {stars} ⭐\n"
            "*Vencimiento:* {expires_at}\n"
            f"{_SEP_DIVIDER}\n"
            "🌐 *Disfruta de datos ilimitados!*\n"
        )

        @classmethod
        def subscription_activated(cls, plan_name: str, stars: int, expires_at: str) -> str:
            """Generate subscription activated message."""
            message = cls._HEADER
            message += cls._SUCCESS_BODY.format(
                plan_name=plan_name,
                stars=stars,
                expires_at=expires_at,
            )
            return message

    class Error:
        """Mensajes de error."""

        ALREADY_ACTIVE = (
            f"{_SEP_HEADER}\n"
            "⚠️ *YA TIENES SUSCRIPCIÓN ACTIVA*\n"
            f"{_SEP_HEADER}\n"
            "\n"
            "Ya cuentas con una suscripción premium activa.\n"
            "Debes esperar a que venza para comprar una nueva.\n"
            f"{_SEP_DIVIDER}\n"
        )

        INSUFFICIENT_STARS = (
            f"{_SEP_HEADER}\n"
            "❌ *STARS INSUFICIENTES*\n"
            f"{_SEP_HEADER}\n"
            "\n"
            "No tienes suficientes Stars para esta compra.\n"
            "Recarga tu saldo e inténtalo nuevamente.\n"
            f"{_SEP_DIVIDER}\n"
        )

        INVALID_PLAN = (
            f"{_SEP_HEADER}\n"
            "❌ *PLAN INVÁLIDO*\n"
            f"{_SEP_HEADER}\n"
            "\n"
            "El plan seleccionado no existe.\n"
            "Por favor, selecciona un plan válido.\n"
            f"{_SEP_DIVIDER}\n"
        )
