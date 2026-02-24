"""
Mensajes para gestión avanzada de llaves VPN de uSipipo.

Author: uSipipo Team
Version: 2.0.0 - Feature-based architecture
"""


class KeyManagementMessages:
    """Mensajes para gestión de llaves VPN."""

    # ============================================
    # MAIN MENU
    # ============================================

    MAIN_MENU = (
        "🔑 **Gestión de Llaves VPN**\n\n"
        "📊 **Resumen de tus llaves:**\n"
        "• **Total:** {total_keys} llaves\n"
        "• **Outline:** {outline_count} llaves\n"
        "• **WireGuard:** {wireguard_count} llaves\n\n"
        "Selecciona una opción para gestionar tus accesos:"
    )

    NO_KEYS = (
        "📭 **Sin Llaves VPN**\n\n"
        "No tienes llaves VPN activas.\n\n"
        "💡 Crea una nueva llave para comenzar a usar el servicio."
    )

    BACK_TO_MAIN = "🔙 Volviendo al menú principal..."

    # ============================================
    # KEYS LIST
    # ============================================

    KEYS_LIST_HEADER = "🔑 **Tus llaves {type}**\n\n"

    NO_KEYS_TYPE = (
        "📭 **Sin llaves {type}**\n\n"
        "No tienes llaves {type} activas.\n\n"
        "💡 Crea una nueva llave para comenzar."
    )

    NO_KEYS_STATS = (
        "📭 **Sin estadísticas**\n\n" "No tienes llaves para mostrar estadísticas."
    )

    # ============================================
    # KEY DETAILS
    # ============================================

    KEY_DETAILS = (
        "💎 **{name}**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📡 **Protocolo:** `{type}`\n"
        "🖥️ **Servidor:** `{server}`\n"
        "📊 **Consumo de Datos:**\n"
        "{usage_bar}\n"
        "   `{usage:.2f} / {limit:.2f} GB ({percentage:.1f}%)`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🟢 **Estado:** {status}\n"
        "📅 **Expiración:** {expires}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Selecciona una acción:"
    )

    KEY_NOT_FOUND = (
        "❌ **Llave no encontrada**\n\n"
        "La llave que buscas no existe o no te pertenece."
    )

    # ============================================
    # STATISTICS
    # ============================================

    STATISTICS = (
        "📊 **Estadísticas de Uso**\n\n"
        "🔑 **Total de llaves:** {total_keys}\n"
        "✅ **Llaves activas:** {active_keys}\n"
        "📈 **Uso total:** {total_usage} / {total_limit} GB ({percentage:.1f}%)\n\n"
        "📡 **Por protocolo:**\n"
        "• **Outline:** {outline_count} llaves ({outline_usage} GB)\n"
        "• **WireGuard:** {wireguard_count} llaves ({wireguard_usage} GB)\n\n"
        "💡 Mantén tu uso por debajo del límite para evitar interrupciones."
    )

    # ============================================
    # ACTIONS
    # ============================================

    class Actions:
        """Mensajes de acciones sobre llaves."""

        KEY_SUSPENDED = (
            "⏸️ **Llave Suspendida**\n\n"
            "La llave ha sido suspendida temporalmente.\n\n"
            "🔄 Puedes reactivarla cuando quieras."
        )

        KEY_REACTIVATED = (
            "✅ **Llave Reactivada**\n\n"
            "La llave ha sido reactivada exitosamente.\n\n"
            "🌐 Ya puedes volver a usar tu conexión VPN."
        )

        KEY_DELETED = (
            "🗑️ **Llave Eliminada**\n\n"
            "La llave ha sido eliminada permanentemente.\n\n"
            "⚠️ Todos los dispositivos conectados se desconectarán."
        )

        KEY_RENAMED = (
            "✏️ **Llave Renombrada**\n\n"
            "La llave ahora se llama: **{new_name}**\n\n"
            "✅ Cambio aplicado exitosamente."
        )

        CONFIG_UPDATED = (
            "⚙️ **Configuración Actualizada**\n\n"
            "La configuración de la llave ha sido actualizada.\n\n"
            "🔄 Los cambios se aplicarán en la próxima conexión."
        )

    # ============================================
    # ERRORS
    # ============================================

    class Error:
        """Mensajes de error."""

        SYSTEM_ERROR = (
            "❌ **Error del Sistema**\n\n"
            "No pude procesar tu solicitud.\n\n"
            "Por favor, intenta más tarde."
        )

        KEY_NOT_ACCESSIBLE = (
            "🚫 **Llave no accesible**\n\n"
            "No tienes permisos para acceder a esta llave."
        )

        OPERATION_FAILED = (
            "❌ **Operación Fallida**\n\n"
            "No pude completar la operación solicitada.\n\n"
            "Error: {error}"
        )

        DELETE_NOT_ALLOWED = (
            "🚫 **Eliminación No Permitida**\n\n"
            "Para eliminar llaves, debes haber realizado al menos un depósito.\n\n"
            "💰 **Realiza un depósito** para desbloquear esta función.\n\n"
            "📍 Ve a → 💳 Depositar"
        )

        INVALID_ACTION = (
            "❌ **Acción Inválida**\n\n"
            "La acción solicitada no es válida para esta llave."
        )

        QUOTA_EXCEEDED = (
            "⚠️ **Cuota Excedida**\n\n"
            "Has alcanzado el límite de llaves para tu plan.\n\n"
            "💡 *Soluciones:*\n"
            "• Elimina llaves que no usas\n"
            "• Actualiza tu plan para más llaves"
        )

    # ============================================
    # SUCCESS
    # ============================================

    class Success:
        """Mensajes de éxito."""

        OPERATION_COMPLETED = (
            "✅ **Operación Completada**\n\n" "La acción se ha realizado exitosamente."
        )

        CHANGES_SAVED = (
            "💾 **Cambios Guardados**\n\n" "Tus preferencias han sido actualizadas."
        )

        BACKUP_CREATED = (
            "📦 **Backup Creado**\n\n"
            "Se ha creado una copia de seguridad de tus llaves.\n\n"
            "📁 Archivo: {filename}"
        )
