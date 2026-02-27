"""
Mensajes para gestión avanzada de llaves VPN de uSipipo.

Author: uSipipo Team
Version: 3.2.0 - MarkdownV2 Compatible
"""


class KeyManagementMessages:
    """Mensajes para gestión de llaves VPN - MarkdownV2 Compatible."""

    # ============================================
    # MAIN MENU - MarkdownV2 OK
    # ============================================

    MAIN_MENU = (
        "🔐 *Mis Llaves VPN*\n\n"
        "📊 Resumen:\n"
        "🔑 Total: {total_keys}\n"
        "🌐 Outline: {outline_count}\n"
        "🔒 WireGuard: {wireguard_count}\n\n"
        "⚡ *Elige una opción:*"
    )

    NO_KEYS = (
        "📭 *Sin llaves*\n\n"
        "🔒 No tienes llaves activas\n\n"
        "💡 Crea tu primera llave segura 🚀"
    )

    BACK_TO_MAIN = "🔙 Volviendo al menú..."

    # ============================================
    # KEYS LIST
    # ============================================

    KEYS_LIST_HEADER = "🔑 *Tus llaves {type}*\n\n"

    NO_KEYS_TYPE = (
        "📭 Sin llaves {type}\n\n"
        "💡 Crea una nueva llave para comenzar."
    )

    NO_KEYS_STATS = (
        "📭 *Sin estadísticas*\n\n"
        "No hay llaves para mostrar datos de consumo."
    )

    # ============================================
    # KEY DETAILS - MarkdownV2 OK
    # ============================================

    KEY_DETAILS = (
        "💎 *{name}*\n\n"
        "📡 {type} · 🖥️ {server}\n\n"
        "📊 Consumo: {usage}/{limit}GB ({percentage}%)\n"
        "{usage_bar}\n\n"
        "{status_icon} Estado: *{status}*\n"
        "📅 Expira: {expires}\n\n"
        "⚡ *Acciones:*"
    )

    KEY_NOT_FOUND = (
        "❌ *Llave no encontrada*\n\n"
        "No existe o no te pertenece a tu cuenta."
    )

    # ============================================
    # STATISTICS - MarkdownV2 OK
    # ============================================

    STATISTICS = (
        "📊 Mis Estadísticas\n\n"
        "🔐 Llaves: {total_keys} (🟢 {active_keys} activas)\n\n"
        "📡 Datos: {total_usage}/{total_limit}GB "
        "({percentage}%)\n"
        "{usage_bar}\n\n"
        "🔌 Protocolos:\n"
        "🌐 Outline {outline_count} 💾 {outline_usage}GB\n"
        "🔒 WireGuard {wireguard_count} 💾 {wireguard_usage}GB\n\n"
        "💡 ¡Excelente! Uso menor al 80% 🎯"
    )

    # ============================================
    # ACTIONS - MarkdownV2 OK
    # ============================================

    class Actions:
        """Mensajes de acciones - MarkdownV2 Compatible."""

        KEY_SUSPENDED = (
            "⏸️ *Llave suspendida*\n\n"
            "🔒 Modo reposo activado\n\n"
            "🔄 Puedes reactivarla cuando quieras ⚡"
        )

        KEY_REACTIVATED = (
            "✅ *Llave activada*\n\n"
            "🚀 Conexión lista\n\n"
            "🌐 ¡A navegar seguro\\! 🔥"
        )

        KEY_DELETED = (
            "🗑️ *Llave eliminada*\n\n"
            "💥 Destruida permanentemente\n\n"
            "🔌 Dispositivos desconectados ⚡"
        )

        KEY_RENAMED = (
            "✏️ *Renombrada*\n\n"
            "✨ {new_name}\n\n"
            "✅ Cambio guardado 🎯"
        )

        CONFIG_UPDATED = (
            "⚙️ *Configuración actualizada*\n\n"
            "🔧 Cambios guardados\n\n"
            "🔄 Se aplicarán en la próxima conexión ⚡"
        )

    # ============================================
    # ERRORS - MarkdownV2 OK
    # ============================================

    class Error:
        """Mensajes de error - MarkdownV2 Compatible."""

        SYSTEM_ERROR = (
            "🚨 *Error del sistema*\n\n"
            "💥 Fallo temporal\n\n"
            "🔄 Intenta de nuevo en un momento 📡"
        )

        KEY_NOT_ACCESSIBLE = (
            "🚫 *Acceso denegado*\n\n"
            "🔒 No tienes permisos para esta llave 🔐"
        )

        OPERATION_FAILED = (
            "❌ *Operación fallida*\n\n"
            "💥 No se pudo completar\n\n"
            "📟 {error}"
        )

        DELETE_NOT_ALLOWED = (
            "🔒 *Eliminación bloqueada*\n\n"
            "💰 Requiere depósito previo\n\n"
            "📍 Ve a 💳 *Depositar* 🗝️"
        )

        INVALID_ACTION = (
            "⛔ *Acción inválida*\n\n"
            "🚫 No disponible en este momento"
        )

        QUOTA_EXCEEDED = (
            "⚠️ *Cuota excedida*\n\n"
            "💥 Has alcanzado tu límite\n\n"
            "💡 🗑️ Elimina una llave o ⬆️ mejora tu plan ⚡"
        )

    # ============================================
    # SUCCESS - MarkdownV2 OK
    # ============================================

    class Success:
        """Mensajes de éxito - MarkdownV2 Compatible."""

        OPERATION_COMPLETED = (
            "✅ *Listo*\n\n"
            "⚡ Operación completada 🎯"
        )

        CHANGES_SAVED = (
            "💾 *Guardado*\n\n"
            "✨ Cambios actualizados"
        )

        BACKUP_CREATED = (
            "📦 *Backup creado*\n\n"
            "💾 Copia segura guardada\n\n"
            "📁 {filename}"
        )
