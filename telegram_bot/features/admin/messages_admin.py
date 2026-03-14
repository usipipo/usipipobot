"""
Mensajes para panel administrativo de uSipipo.

Author: uSipipo Team
Version: 3.0.0 - Complete admin management
"""


class AdminMessages:
    """Mensajes para panel administrativo."""

    class Menu:
        """Mensajes del menú administrativo."""

        MAIN = (
            "🔧 **Panel Administrativo**\n\n"
            "Selecciona una opción para gestionar el sistema:\n\n"
            "👥 **Usuarios** - Gestión de cuentas\n"
            "🔑 **Llaves VPN** - Administración de accesos\n"
            "📊 **Dashboard** - Estado y métricas\n"
            "🎫 **Tickets** - Soporte técnico\n"
            "⚙️ **Configuración** - Ajustes del sistema"
        )

    class Users:
        """Mensajes de gestión de usuarios."""

        HEADER = "👥 **Gestión de Usuarios**\n\n"

        NO_USERS = "📭 **Sin Usuarios**\n\nNo hay usuarios registrados en el sistema."

        USER_DETAILS = (
            "👤 **Detalles del Usuario**\n\n"
            "🆔 **ID:** `{user_id}`\n"
            "👤 **Nombre:** {full_name}\n"
            "🔖 **Username:** @{username}\n"
            "📅 **Registro:** {created_at}\n"
            "🟢 **Estado:** {status}\n"
            "🎁 **Créditos Referidos:** {referral_credits}\n"
            "🔑 **Llaves Activas:** {keys_count}"
        )

        CONFIRM_DELETE = (
            "⚠️ **Confirmar Eliminación**\n\n"
            "¿Estás seguro de que deseas eliminar al usuario `{user_id}`?\n\n"
            "🚨 **Esta acción eliminará:**\n"
            "• Todas las llaves VPN del usuario\n"
            "• Historial de transacciones\n"
            "• Datos de referidos\n\n"
            "**Esta acción no se puede deshacer.**"
        )

        USER_SUSPENDED = "⏸️ **Usuario Suspendido**\n\nEl usuario ha sido suspendido exitosamente."
        USER_REACTIVATED = (
            "✅ **Usuario Reactivado**\n\nEl usuario ha sido reactivado exitosamente."
        )
        USER_DELETED = (
            "🗑️ **Usuario Eliminado**\n\nEl usuario y todos sus datos han sido eliminados."
        )

    class Keys:
        """Mensajes de gestión de llaves."""

        HEADER = "🔑 **Gestión de Llaves VPN**\n\n"

        NO_KEYS = "📭 **Sin Llaves**\n\nNo hay llaves VPN registradas en el sistema."

        KEY_DETAILS = (
            "🔑 **Detalles de la Llave**\n\n"
            "🆔 **ID:** `{key_id}`\n"
            "📛 **Nombre:** {name}\n"
            "👤 **Usuario ID:** {user_id}\n"
            "📡 **Protocolo:** {type}\n"
            "🖥️ **Estado Servidor:** {server}\n"
            "📊 **Uso:** {usage} GB\n"
            "🟢 **Estado:** {status}\n"
            "📅 **Creada:** {created_at}\n"
            "⏰ **Expira:** {expires_at}"
        )

        CONFIRM_DELETE = (
            "⚠️ **Confirmar Eliminación**\n\n"
            "¿Estás seguro de que deseas eliminar la llave `{key_id}`?\n\n"
            "**Esta acción no se puede deshacer.**"
        )

        KEY_DELETED = "🗑️ **Llave Eliminada**\n\nLa llave VPN ha sido eliminada exitosamente."
        KEY_SUSPENDED = "⏸️ **Llave Suspendida**\n\nLa llave ha sido suspendida temporalmente."
        KEY_REACTIVATED = "✅ **Llave Reactivada**\n\nLa llave ha sido reactivada exitosamente."

    class Dashboard:
        """Mensajes del dashboard."""

        FULL = (
            "📊 **Dashboard de Administración**\n\n"
            "👥 **Usuarios:**\n"
            "  • Total: `{total_users}`\n"
            "  • Activos: `{active_users}`\n"
            "  • Nuevos hoy: `{new_users_today}`\n\n"
            "🔑 **Llaves VPN:**\n"
            "  • Total: `{total_keys}`\n"
            "  • Activas: `{active_keys}`\n"
            "  • Creadas hoy: `{keys_created_today}`\n"
            "  • ⚡ WireGuard: `{wireguard_keys}`\n"
            "  • 🔵 Outline: `{outline_keys}`\n\n"
            "💰 **Ingresos:** `{total_revenue}` ⭐\n\n"
            "🖥️ **Servidores:** {server_status}\n\n"
            "_Actualizado: {generated_at}_"
        )

    class Server:
        """Mensajes de estado del servidor."""

        HEADER = "📊 **Estado del Servidor**\n\n"

        SYSTEM_HEALTHY = (
            "✅ **Sistema Saludable**\n\nTodos los servicios funcionando correctamente."
        )
        SYSTEM_WARNING = (
            "⚠️ **Advertencia del Sistema**\n\nSe detectaron problemas que requieren atención."
        )
        SYSTEM_CRITICAL = "🚨 **Estado Crítico**\n\nSe requieren acciones inmediatas."

        RESTART_SUCCESS = "🔄 **Servicio Reiniciado**\n\nEl servicio se ha reiniciado exitosamente."
        MAINTENANCE_MODE = "🔧 **Modo Mantenimiento**\n\nEl sistema está en modo mantenimiento."

    class Settings:
        """Mensajes de configuración."""

        HEADER = "⚙️ **Configuración del Sistema**\n\n"

        SERVERS = (
            "🌐 **Configuración de Servidores**\n\n"
            "⚡ **WireGuard:**\n"
            "  • Estado: {wg_status}\n"
            "  • Llaves activas: {wg_keys}\n\n"
            "🔵 **Outline:**\n"
            "  • Estado: {ol_status}\n"
            "  • Llaves activas: {ol_keys}"
        )

        LIMITS = (
            "📊 **Límites del Sistema**\n\n"
            "• Límite de llaves por usuario: {max_keys}\n"
            "• Límite de datos gratuito: {free_data} GB\n"
            "• Datos de referido: {referral_data} GB"
        )

    class Maintenance:
        """Mensajes de mantenimiento."""

        HEADER = "🔧 **Mantenimiento del Sistema**\n\n"

        RESTART_RESULTS = (
            "🔄 **Resultados del Reinicio**\n\n"
            "⚡ **WireGuard:** {wireguard}\n"
            "🔵 **Outline:** {outline}"
        )

        BACKUP_CREATED = (
            "📦 **Backup Creado**\n\n"
            "Se ha creado una copia de seguridad.\n"
            "📁 Archivo: `{filename}`"
        )

        LOGS_CLEARED = (
            "🧹 **Logs Limpiados**\n\nLos archivos de log han sido limpiados exitosamente."
        )

    class Error:
        """Mensajes de error."""

        SYSTEM_ERROR = (
            "❌ **Error del Sistema**\n\n"
            "No pude completar la operación solicitada.\n\n"
            "Por favor, revisa los logs e intenta más tarde."
        )

        ACCESS_DENIED = (
            "🚫 **Acceso Denegado**\n\n"
            "No tienes permisos para realizar esta acción.\n\n"
            "Esta función está reservada para administradores."
        )

        USER_NOT_FOUND = (
            "❌ **Usuario No Encontrado**\n\nEl usuario especificado no existe en el sistema."
        )
        KEY_NOT_FOUND = (
            "❌ **Llave No Encontrada**\n\nLa llave especificada no existe en el sistema."
        )

        OPERATION_FAILED = (
            "❌ **Operación Fallida**\n\nNo se pudo completar la operación.\n\nError: {error}"
        )

    class Success:
        """Mensajes de éxito."""

        OPERATION_COMPLETED = (
            "✅ **Operación Completada**\n\nLa acción se ha realizado exitosamente."
        )
        OPERATION_CANCELLED = "❌ **Operación Cancelada**\n\nLa acción ha sido cancelada."

        CHANGES_SAVED = (
            "💾 **Cambios Guardados**\n\nLa configuración ha sido actualizada correctamente."
        )

        BACKUP_CREATED = (
            "📦 **Backup Creado**\n\n"
            "Se ha creado una copia de seguridad exitosamente.\n"
            "📁 Archivo: {filename}"
        )

    class Logs:
        """Mensajes de gestión de logs."""

        HEADER = "📋 **Logs del Sistema**\n\n"

        NO_LOGS = "📭 **Sin Logs**\n\nNo hay archivos de logs disponibles."

        LOGS_DISPLAY = (
            "📋 **Últimas Líneas de Log**\n\n"
            "```\n{logs_content}\n```\n\n"
            "📅 *Extraído: {timestamp}*"
        )

        LOGS_ERROR = (
            "❌ **Error al Leer Logs**\n\n"
            "No se pudieron leer los archivos de log.\n"
            "Error: {error}"
        )

        LOGS_CLEARED = (
            "🧹 **Logs Limpiados**\n\nLos archivos de log han sido limpiados exitosamente."
        )
