"""
Mensajes para gestión de usuarios de uSipipo.

Author: uSipipo Team
Version: 2.0.0 - Feature-based architecture
"""

from datetime import datetime, timezone


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
            "• Cada clave tiene 10GB de datos\n"
            "• Usa el menú Operaciones para más opciones"
        )

        FAQ_TEXT = (
            "📚 *Preguntas Frecuentes*\n\n"
            "❓ *¿Cómo configuro mi VPN?*\n"
            "Descarga la app WireGuard o Outline, importa tu clave y conecta\\.\n\n"
            "❓ *¿Cuántos dispositivos puedo usar?*\n"
            "Puedes crear hasta 2 claves gratuitas\\. Cada clave = 1 dispositivo\\.\n\n"
            "❓ *¿Qué pasa si agoto mis datos?*\n"
            "Compra más GB desde el menú principal con Telegram Stars\\.\n\n"
            "❓ *¿Cómo funciona el programa de referidos?*\n"
            "Comparte tu código de referido\\. Cuando alguien se registra, ambos reciben créditos\\.\n\n"
            "❓ *¿Necesitas más ayuda?*\n"
            "Crea un ticket de soporte y te responderemos pronto\\."
        )

        SUPPORT_PROMPT = (
            "🎫 *Soporte Técnico*\n\n"
            "¿Tienes un problema que no puedes resolver?\n\n"
            "Crea un ticket y nuestro equipo te ayudará:\n"
            "• Problemas de conexión\n"
            "• Errores en pagos\n"
            "• Solicitudes especiales\n"
            "• Reporte de bugs\n\n"
            "_Respuesta en menos de 24 horas_"
        )

        TICKET_CREATED = (
            "✅ *Ticket Creado*\n\n"
            "Tu ticket \\#{ticket_id} ha sido enviado\\.\n\n"
            "Te responderemos lo antes posible\\.\n\n"
            "Estado: 🟡 Pendiente"
        )

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

            return (
                f"┌──────────────────────────┐\n"
                f"│ 👤 {name[:18]:<18} │\n"
                f"│ 🆔 `{user_id}`{' ' * (18 - len(str(user_id)))}│\n"
                f"│ 📅 {join_date}{' ' * (16 - len(join_date))}│\n"
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
