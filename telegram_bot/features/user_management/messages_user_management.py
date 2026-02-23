"""
Mensajes para gestión de usuarios de uSipipo.

Author: uSipipo Team
Version: 2.0.0 - Feature-based architecture
"""


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
            "• 10 GB de datos por llave\n\n"
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
        """Mensajes de información del usuario."""

        HEADER = "ℹ️ **Información de tu Cuenta**"

        USER_INFO = (
            "ℹ️ *Información Detallada*\n\n"
            "👤 *Usuario:* {name}\n"
            "🆔 *ID:* {user_id}\n"
            "👥 *Username:* @{username}\n"
            "📅 *Registro:* {join_date}\n"
            "🟢 *Estado:* {status}\n\n"
            "📊 *Datos:*\n"
            "├─ Usados: {data_used}\n"
            "├─ Gratuitos restantes: {free_data_remaining}\n"
            "└─ Paquetes activos: {active_packages}\n\n"
            "🔑 *Claves VPN:*\n"
            "└─ Usadas: {keys_used}/{keys_total}\n\n"
            "🎁 *Referidos:*\n"
            "├─ Código: {referral_code}\n"
            "├─ Invitados: {total_referrals}\n"
            "└─ Créditos: {credits}"
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
            "{number}\\. `{date}` \\- {description}\n"
            "   {amount} | {status}"
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
