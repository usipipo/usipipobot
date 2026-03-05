"""
Messages for admin VPN management.

Author: uSipipo Team
Version: 1.0.0 - VPN Server Management
"""


class AdminVpnMessages:
    """Messages for admin VPN management."""

    MAIN_MENU = (
        "⚡ **Gestión de Servidores VPN**\n\n"
        "Selecciona una opción para administrar los servidores:\n\n"
        "📊 **Estado Servidores** - Ver salud de WireGuard y Outline\n"
        "⚡ **Gestionar WireGuard** - Administrar claves WireGuard\n"
        "🔵 **Gestionar Outline** - Administrar claves Outline\n"
        "🧹 **Limpieza Claves Fantasmas** - Deshabilitar claves inactivas"
    )

    SERVER_STATUS = (
        "📊 **Estado de Servidores VPN**\n\n"
        "⚡ **WireGuard:**\n"
        "  • Estado: {wg_health}\n"
        "  • Total claves: {wg_total}\n"
        "  • Claves activas: {wg_active}\n\n"
        "🔵 **Outline:**\n"
        "  • Estado: {ol_health}\n"
        "  • Servidor: {ol_name}\n"
        "  • Total claves: {ol_total}\n"
        "  • Claves activas: {ol_active}\n\n"
        "_Última actualización: {timestamp}_"
    )

    KEYS_LIST_HEADER = "🔑 **Lista de Claves {server_type}**\n\n"

    NO_KEYS = (
        "📭 **Sin Claves**\n\n" "No hay claves {server_type} registradas en el sistema."
    )

    KEY_DETAILS = (
        "🔑 **Detalles de la Clave**\n\n"
        "🆔 **ID:** `{key_id}`\n"
        "📛 **Nombre:** {name}\n"
        "👤 **Usuario ID:** {user_id}\n"
        "📡 **Tipo:** {key_type}\n"
        "📊 **Uso:** {used_bytes} bytes\n"
        "🟢 **Estado:** {status}\n"
        "👁️ **Última vista:** {last_seen}\n"
        "📅 **Creada:** {created_at}"
    )

    CLEANUP_REPORT = (
        "🧹 **Reporte de Limpieza de Claves Fantasmas**\n\n"
        "📊 **Resumen:**\n"
        "  • Claves revisadas: {total_checked}\n"
        "  • Fantasmas encontrados: {ghosts_found}\n"
        "  • Deshabilitados: {disabled_count}\n\n"
        "{errors_section}"
    )

    CLEANUP_ERRORS = "⚠️ **Errores durante la limpieza:**\n" "{errors}"

    NO_GHOST_KEYS = (
        "✅ **Sin Claves Fantasmas**\n\n"
        "No se encontraron claves inactivas que requieran limpieza."
    )

    # Success messages
    KEY_ENABLED = (
        "✅ **Clave Habilitada**\n\n"
        "La clave ha sido habilitada exitosamente en el servidor."
    )

    KEY_DISABLED = (
        "⏸️ **Clave Deshabilitada**\n\n"
        "La clave ha sido deshabilitada exitosamente en el servidor."
    )

    KEY_DELETED = (
        "🗑️ **Clave Eliminada**\n\n"
        "La clave ha sido eliminada completamente del servidor y la base de datos."
    )

    OPERATION_CANCELLED = (
        "❌ **Operación Cancelada**\n\n" "La acción ha sido cancelada."
    )

    # Error messages
    ERROR_KEY_NOT_FOUND = (
        "❌ **Clave No Encontrada**\n\n"
        "La clave especificada no existe en el sistema."
    )

    ERROR_SERVER_UNAVAILABLE = (
        "❌ **Servidor No Disponible**\n\n"
        "No se pudo conectar con el servidor {server_type}. "
        "Verifica la configuración e intenta nuevamente."
    )

    ERROR_OPERATION_FAILED = (
        "❌ **Operación Fallida**\n\n"
        "No se pudo completar la operación.\n"
        "Error: {error}"
    )

    CONFIRM_DELETE_KEY = (
        "⚠️ **Confirmar Eliminación**\n\n"
        "¿Estás seguro de que deseas eliminar la clave `{key_id}`?\n\n"
        "🚨 **Esta acción eliminará:**\n"
        "• La clave del servidor VPN\n"
        "• La clave de la base de datos\n\n"
        "**Esta acción no se puede deshacer.**"
    )

    SERVER_MANAGE_HEADER = (
        "⚡ **Gestión de {server_type}**\n\n"
        "Selecciona una acción para administrar las claves."
    )
