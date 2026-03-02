"""
Mensajes para gestión de usuarios de uSipipo.

Author: uSipipo Team
Version: 2.0.0 - Feature-based architecture
"""

from datetime import datetime, timezone

from utils.message_separators import (
    MessageSeparatorBuilder,
    TELEGRAM_MOBILE_WIDTH,
    compact_separator,
)


def _progress_bar(percentage: float, width: int = 10) -> str:
    """Genera barra de progreso ASCII estilo cyberpunk."""
    percentage = max(0, min(100, percentage))
    filled = int(width * percentage / 100)
    return "▓" * filled + "░" * (width - filled)


def _format_key_slots(used: int, total: int) -> str:
    """Genera representación visual de slots de claves."""
    slots = []
    for i in range(min(total, 5)):
        if i < used:
            slots.append("●")
        else:
            slots.append("○")
    return "".join(slots)


# ============================================
# SEPARADORES VISUALES
# ============================================

_SEP_HEADER = (
    MessageSeparatorBuilder()
    .compact().style("double").length(TELEGRAM_MOBILE_WIDTH).build()
)
_SEP_DIVIDER = (
    MessageSeparatorBuilder()
    .compact().style("simple").length(TELEGRAM_MOBILE_WIDTH).build()
)
_SEP_BOLD = (
    MessageSeparatorBuilder()
    .compact().style("bold").length(9).build()
)


class UserManagementMessages:
    """Mensajes para gestión de usuarios."""

    # ============================================
    # WELCOME & ONBOARDING
    # ============================================

    class Welcome:
        """Mensajes de bienvenida y onboarding."""

        NEW_USER = (
            "🎉 ¡Bienvenido, **{name}**!\n\n"
            "Tu cuenta ha sido creada exitosamente.\n\n"
            "🎁 **Regalo de bienvenida:**\n"
            "• 2 llaves VPN gratuitas\n"
            "• 5 GB de datos por llave\n\n"
            "📱 Toca **➕ Crear Nueva** para generar tu primera conexión."
        )

        RETURNING_USER = (
            "👋 ¡Hola de nuevo, **{name}**!\n\n"
            "Todo listo para continuar.\n\n"
            "📊 Usa el menú para gestionar tus accesos."
        )

        NEW_USER_SIMPLIFIED = (
            "🎉 *¡Bienvenido a uSipipo!*\n\n"
            "Tu VPN personal está lista para usar.\n\n"
            "📱 *Usa el menú de abajo para:*\n"
            "• Ver tus claves VPN activas\n"
            "• Crear nuevas claves\n"
            "• Gestionar créditos y compras\n"
            "• Ver tu consumo\n\n"
            "¿Necesitas ayuda? Presiona el botón ❓"
        )

        RETURNING_USER_SIMPLIFIED = (
            "👋 *¡Bienvenido de vuelta!*\n\n"
            "Usa el menú de abajo para gestionar tu VPN:\n"
        )

        HELP_TEXT = (
            "❓ *Centro de Ayuda de uSipipo*\n\n"
            "📱 *Guía Rápida:*\n"
            "🔑 _Mis Claves VPN_ - Ver todas tus claves activas\n"
            "➕ _Nueva Clave_ - Crear una nueva clave VPN\n"
            "⚙️ _Operaciones_ - Créditos, Shop, Referidos\n"
            "💾 _Mis Datos_ - Ver tu consumo actual\n\n"
            "💡 *Consejos:*\n"
            "• Puedes crear hasta 2 claves gratis\n"
            "• Cada clave tiene 5GB de datos\n"
            "• Usa el menú Operaciones para más opciones"
        )

        FAQ_TEXT = (
            f"{_SEP_HEADER}\n"
            "📚 *PREGUNTAS FRECUENTES*\n"
            f"{_SEP_HEADER}\n"
            "\n"
            f"{compact_separator('double', 7, '⚙️')}\n"
            "*¿Cómo configuro mi VPN?*\n"
            f"{compact_separator('double', 7, '⚙️')}\n"
            "\n"
            "│\n"
            "├─ 1️⃣ Descarga *WireGuard* u *Outline*\n"
            "│\n"
            "├─ 2️⃣ Importa tu clave desde el bot\n"
            "│\n"
            "└─ 3️⃣ Conecta y ¡navega seguro!\n"
            "\n"
            f"{_SEP_DIVIDER}\n"
            "\n"
            f"{compact_separator('double', 7, '📱')}\n"
            "*¿Cuántos dispositivos?*\n"
            f"{compact_separator('double', 7, '📱')}\n"
            "\n"
            "│\n"
            "├─ 🆓 *2 claves* gratuitas\n"
            "│   └─ 1 clave = 1 dispositivo\n"
            "│\n"
            "└─ 💎 Más claves en *Shop*\n"
            "\n"
            f"{_SEP_DIVIDER}\n"
            "\n"
            f"{compact_separator('double', 7, '💾')}\n"
            "*¿Agotaste tus datos?*\n"
            f"{compact_separator('double', 7, '💾')}\n"
            "\n"
            "│\n"
            "├─ 🛒 Ve al *menú principal*\n"
            "│\n"
            "├─ ⭐ Compra con *Telegram Stars*\n"
            "│\n"
            "└─ ⚡ Recibe los GB al instante\n"
            "\n"
            f"{_SEP_DIVIDER}\n"
            "\n"
            f"{compact_separator('double', 7, '🎁')}\n"
            "*¿Cómo funcionan los bonos?*\n"
            f"{compact_separator('double', 7, '🎁')}\n"
            "\n"
            "│\n"
            "├─ 🆕 *Bienvenida:* +20% primera compra\n"
            "│\n"
            "├─ ⭐ *Fidelidad:* Compras 3, 5 y 10\n"
            "│   └─ Hasta +50% acumulativo\n"
            "│\n"
            "├─ ⚡ *Recarga Rápida:* +15% (7 días antes)\n"
            "│\n"
            "└─ 👥 *Referidos:* +5GB por cada uno\n"
            "\n"
            f"{_SEP_DIVIDER}\n"
            "\n"
            f"{compact_separator('double', 7, '🔗')}\n"
            "*¿Cómo funcionan los referidos?*\n"
            f"{compact_separator('double', 7, '🔗')}\n"
            "\n"
            "│\n"
            "├─ 📤 Comparte tu *código*\n"
            "│\n"
            "├─ 📝 Alguien se *registra* con él\n"
            "│\n"
            "└─ 🎉 ¡Ambos reciben *créditos!*\n"
            "\n"
            f"{_SEP_HEADER}\n"
        )

        class Bonuses:
            """Mensajes del sistema de bonos con diseño visual mejorado."""

            _SEP_CROWN = compact_separator("bold", 7, "👑")
            _SEP_GIFT = compact_separator("double", 7, "🎁")
            _SEP_STAR = compact_separator("double", 7, "⭐")
            _SEP_BOLT = compact_separator("double", 7, "⚡")
            _SEP_USERS = compact_separator("double", 7, "👥")
            _SEP_TIP = compact_separator("bold", 7, "💡")
            _SEP_DIV = (
                MessageSeparatorBuilder()
                .compact().style("simple").length(TELEGRAM_MOBILE_WIDTH).build()
            )

            @classmethod
            def info(cls) -> str:
                """Mensaje completo del sistema de bonos."""
                return (
                    f"{cls._SEP_CROWN}\n"
                    "*SISTEMA DE BONOS*\n"
                    f"{cls._SEP_CROWN}\n"
                    "\n"
                    f"{cls._SEP_GIFT}\n"
                    "*💫 Bono de Bienvenida*\n"
                    f"{cls._SEP_GIFT}\n"
                    "\n"
                    "│\n"
                    "├─ 🆕 *+20%* datos primera compra\n"
                    "│   └─ Ej: 10GB → *12GB*\n"
                    "│\n"
                    f"{cls._SEP_DIV}\n"
                    "\n"
                    f"{cls._SEP_STAR}\n"
                    "*⭐ Bono de Fidelidad*\n"
                    f"{cls._SEP_STAR}\n"
                    "\n"
                    "│\n"
                    "├─ 🥉 *3ra* compra: +10%\n"
                    "│\n"
                    "├─ 🥈 *5ta* compra: +15%\n"
                    "│\n"
                    "├─ 🥇 *10ma* compra: +25%\n"
                    "│\n"
                    "└─ 📊 *Total máximo:* +50%\n"
                    "\n"
                    f"{cls._SEP_DIV}\n"
                    "\n"
                    f"{cls._SEP_BOLT}\n"
                    "*⚡ Bono Recarga Rápida*\n"
                    f"{cls._SEP_BOLT}\n"
                    "\n"
                    "│\n"
                    "├─ 🗓️ Renueva *7 días antes*\n"
                    "│\n"
                    "└─ 🎁 Obtén *+15%* extra\n"
                    "\n"
                    f"{cls._SEP_DIV}\n"
                    "\n"
                    f"{cls._SEP_USERS}\n"
                    "*👥 Bono por Referidos*\n"
                    f"{cls._SEP_USERS}\n"
                    "\n"
                    "│\n"
                    "├─ 👤 *+5GB* por referido\n"
                    "│   └─ Que realice una compra\n"
                    "│\n"
                    "└─ ♾️ *Sin límite* de referidos\n"
                    "\n"
                    f"{cls._SEP_TIP}\n"
                    "*💡 COMBINA BONOS*\n"
                    f"{cls._SEP_TIP}\n"
                    "\n"
                    "🚀 *Hasta +85%* datos extra\n"
                    "_¡Aprovecha todos los bonos!_"
                )

        BONUSES_INFO = Bonuses.info()

    # ============================================
    # STATUS
    # ============================================

    class Status:
        """Mensajes de estado del usuario."""

        HEADER = "📊 **Estado de tu Cuenta**"

        USER_INFO = (
            "👤 **Usuario:** {name}\n"
            "🆔 **ID:** {user_id}\n"
            "📅 **Fecha de registro:** {join_date}\n"
            "🟢 **Estado:** {status}"
        )

        ADMIN_DASHBOARD = (
            "🔧 **Panel Administrativo**\n\n"
            "👋 **Admin:** {name}\n\n"
            "📊 **Estadísticas Generales:**\n"
            "👥 **Usuarios totales:** {total_users}\n"
            "✅ **Usuarios activos:** {active_users}\n"
            "🔑 **Llaves totales:** {total_keys}\n"
            "🟢 **Llaves activas:** {active_keys}\n"
            "📈 **Carga del servidor:** {server_load}"
        )

    # ============================================
    # INFO
    # ============================================

    class Info:
        """Mensajes de información del usuario - Estilo Cyberpunk Mobile-First."""

        HEADER = "👤 𝙿𝚁𝙾𝙵𝙸𝙻𝙴 𝚂𝚈𝚂𝚃𝙴𝙼"

        @staticmethod
        def USER_INFO(
            name: str,
            user_id: int,
            username: str,
            join_date: str,
            days_since_join: int,
            status: str,
            data_used: str,
            data_total: str,
            data_percentage: float,
            free_data_remaining: str,
            active_packages: int,
            keys_used: int,
            keys_total: int,
            referral_code: str,
            total_referrals: int,
            credits: int,
        ) -> str:
            remaining_slots = keys_total - keys_used
            status_icon = "⬡" if "Activo" in status else "⬢"

            progress = _progress_bar(data_percentage)
            key_slots = _format_key_slots(keys_used, keys_total)

            date_display = f"{join_date} ({days_since_join}d)"

            return (
                f"┌──────────────────────────┐\n"
                f"│ 👤 {name[:18]:<18} │\n"
                f"│ 🆔 `{user_id}`{' ' * (18 - len(str(user_id)))}│\n"
                f"│ 📅 {date_display}{' ' * (16 - len(date_display))}│\n"
                f"│ 🔰 {status_icon} {status}{' ' * (15 - len(f'{status_icon} {status}'))}│\n"
                f"└──────────────────────────┘\n"
                f"\n"
                f"📊 *DATA METRICS*\n"
                f"`{progress}` {data_percentage:.0f}%\n"
                f"├ Usado: {data_used}\n"
                f"├ Libre: {free_data_remaining}\n"
                f"└ Paquetes: {active_packages}\n"
                f"\n"
                f"🔑 *KEY MATRIX*\n"
                f"`{key_slots}` {keys_used}/{keys_total} slots\n"
                f"└ Disponibles: {remaining_slots}\n"
                f"\n"
                f"🎁 *REFERRAL NETWORK*\n"
                f"├ Código: `{referral_code}`\n"
                f"├ Invitados: {total_referrals}\n"
                f"└ Créditos: {credits} ⭐"
            )

    # ============================================
    # HISTORY
    # ============================================

    class History:
        """Mensajes de historial de transacciones."""

        HEADER = "📜 *Historial de Transacciones*\n\n"

        NO_TRANSACTIONS = (
            "📜 *Historial de Transacciones*\n\n"
            "No tienes transacciones registradas aún."
        )

        TRANSACTION_ITEM = (
            "{number}\\. `{date}` \\- {description}\n" "   {amount} | {status}"
        )

        FOOTER = "\n\n📄 _Ver más_ | 🏠 _Menú principal_"

    # ============================================
    # ERRORS
    # ============================================

    class Error:
        """Mensajes de error."""

        REGISTRATION_FAILED = (
            "❌ **Error en el registro**\n\n"
            "No pude crear tu cuenta. Por favor, intenta más tarde.\n"
            "Si el problema persiste, contacta soporte."
        )

        STATUS_FAILED = (
            "❌ **Error obteniendo estado**\n\n"
            "No pude cargar tu información. Intenta más tarde."
        )

        INFO_FAILED = (
            "❌ **Error obteniendo información**\n\n"
            "No pude cargar tu información detallada. Intenta más tarde."
        )
