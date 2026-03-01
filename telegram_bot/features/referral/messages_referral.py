"""
Mensajes para el modulo de referidos.

Author: uSipipo Team
Version: 1.0.0
"""

from config import settings


class ReferralMessages:
    """Mensajes del sistema de referidos."""

    class Menu:
        HEADER = "🎁 *Sistema de Referidos*"

        @staticmethod
        def referral_info(
            code: str, credits: int, total_referrals: int, bot_username: str
        ) -> str:
            return f"""
{ReferralMessages.Menu.HEADER}

📋 *Tu codigo de referido:* `{code}`

🔗 *Comparte este link:*
`https://t.me/{bot_username}?start={code}`

📊 *Tus estadisticas:*
• Creditos disponibles: *{credits}*
• Referidos exitosos: *{total_referrals}*

💡 *Como funciona?*
1. Comparte tu codigo con amigos
2. Cuando se registran, recibes *{settings.REFERRAL_CREDITS_PER_REFERRAL} creditos*
3. Ellos reciben *{settings.REFERRAL_BONUS_NEW_USER} creditos* de bienvenida
"""

    class Redeem:
        HEADER = "💳 *Canjear Creditos*"

        OPTIONS = f"""
{HEADER}

💰 *Opciones de canje:*

• 📦 *1 GB Extra* - {settings.REFERRAL_CREDITS_PER_GB} creditos
• 🔑 *+1 Slot de Clave* - {settings.REFERRAL_CREDITS_PER_SLOT} creditos

📊 Selecciona que quieres canjear:
"""

        INSUFFICIENT_CREDITS = """
❌ *Creditos insuficientes*

No tienes suficientes creditos para este canje.
"""

        @staticmethod
        def insufficient_for_slot(required: int, current: int) -> str:
            return f"""
❌ *Creditos insuficientes*

Necesitas *{required} creditos* para +1 slot.
Tienes *{current} creditos*.
"""

        @staticmethod
        def confirm_data(credits: int, gb: int) -> str:
            return f"""
✅ *Confirmar Canje*

Vas a canjear *{credits} creditos* por *{gb} GB* de datos extra.

Continuar?
"""

        @staticmethod
        def confirm_slot(credits: int) -> str:
            return f"""
✅ *Confirmar Canje*

Vas a canjear *{credits} creditos* por *+1 slot de clave*.

Continuar?
"""

    class Success:
        @staticmethod
        def data_redeemed(gb: int, remaining: int) -> str:
            return f"""
✅ *Canje exitoso!*

📦 Has recibido *{gb} GB* de datos extra.
💰 Creditos restantes: *{remaining}*
"""

        @staticmethod
        def slot_redeemed(remaining: int) -> str:
            return f"""
✅ *Canje exitoso!*

🔑 Ahora puedes crear *+1 clave adicional*.
💰 Creditos restantes: *{remaining}*
"""

    class Error:
        USER_NOT_FOUND = "❌ Usuario no encontrado."
        SYSTEM_ERROR = "❌ Error del sistema. Intenta nuevamente."
        INSUFFICIENT_CREDITS = "❌ No tienes suficientes creditos."
        INVALID_ACTION = "❌ Accion invalida."

    class Info:
        @staticmethod
        def credits_required_for_gb() -> int:
            return settings.REFERRAL_CREDITS_PER_GB

        @staticmethod
        def credits_required_for_slot() -> int:
            return settings.REFERRAL_CREDITS_PER_SLOT

    class Share:
        @staticmethod
        def get_share_text(code: str, bot_username: str) -> str:
            return (
                f"¡Usa mi código de referido y obtén {settings.REFERRAL_BONUS_NEW_USER} créditos "
                f"gratis para uSipipo VPN! 🚀\n\n"
                f"👉 https://t.me/{bot_username}?start={code}"
            )

        @staticmethod
        def get_share_url(code: str, bot_username: str) -> str:
            share_text = ReferralMessages.Share.get_share_text(code, bot_username)
            encoded_text = (
                share_text.replace(" ", "%20").replace("\n", "%0A").replace("!", "%21")
            )
            return f"https://t.me/share/url?url=&text={encoded_text}"
