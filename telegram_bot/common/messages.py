"""
Common messages shared across all features.

Author: uSipipo Team
Version: 1.0.0 - Common Components
"""


class CommonMessages:
    """Common messages used across all features."""

    # ============================================
    # NAVIGATION
    # ============================================

    class Navigation:
        """Navigation messages."""

        BACK_TO_MAIN = "🔙 Volviendo al menú principal..."
        BACK_TO_PREVIOUS = "🔙 Volviendo al menú anterior..."
        OPERATION_CANCELLED = "❌ Operación cancelada."
        MAIN_MENU_HINT = "💡 Usa el menú principal para navegar."

    # ============================================
    # ERRORS
    # ============================================

    class Error:
        """Error messages."""

        SYSTEM_ERROR = (
            "❌ **Error del Sistema**\n\n"
            "No pude completar la operación solicitada.\n\n"
            "Por favor, intenta más tarde o contacta soporte."
        )

        ACCESS_DENIED = (
            "🚫 **Acceso Denegado**\n\n"
            "No tienes permisos para realizar esta acción.\n\n"
            "Esta función está reservada para administradores."
        )

        NOT_FOUND = (
            "❌ **No Encontrado**\n\n"
            "El elemento solicitado no existe.\n\n"
            "Por favor, verifica e intenta nuevamente."
        )

        VALIDATION_ERROR = (
            "⚠️ **Error de Validación**\n\n"
            "Los datos proporcionados no son válidos.\n\n"
            "Por favor, verifica e intenta nuevamente."
        )

        NETWORK_ERROR = (
            "🌐 **Error de Conexión**\n\n"
            "No pude conectar con el servidor.\n\n"
            "Por favor, verifica tu conexión e intenta nuevamente."
        )

        PERMISSION_DENIED = (
            "🔒 **Permiso Denegado**\n\n"
            "No tienes los permisos necesarios para esta acción."
        )

        RATE_LIMIT = (
            "⏱️ **Límite Alcanzado**\n\n"
            "Has alcanzado el límite de solicitudes.\n\n"
            "Por favor, espera un momento antes de continuar."
        )

    # ============================================
    # SUCCESS
    # ============================================

    class Success:
        """Success messages."""

        OPERATION_COMPLETED = (
            "✅ **Operación Completada**\n\n" "La acción se ha realizado exitosamente."
        )

        CHANGES_SAVED = (
            "💾 **Cambios Guardados**\n\n"
            "Los cambios han sido guardados correctamente."
        )

        CREATED_SUCCESSFULLY = (
            "🎉 **Creado Exitosamente**\n\n" "El elemento ha sido creado correctamente."
        )

        UPDATED_SUCCESSFULLY = (
            "🔄 **Actualizado Exitosamente**\n\n"
            "El elemento ha sido actualizado correctamente."
        )

        DELETED_SUCCESSFULLY = (
            "🗑️ **Eliminado Exitosamente**\n\n"
            "El elemento ha sido eliminado correctamente."
        )

    # ============================================
    # CONFIRMATION
    # ============================================

    class Confirmation:
        """Confirmation messages."""

        DELETE_CONFIRM = (
            "⚠️ **Confirmar Eliminación**\n\n"
            "¿Estás seguro de que deseas eliminar este elemento?\n\n"
            "Esta acción no se puede deshacer."
        )

        ACTION_CONFIRM = (
            "❓ **Confirmar Acción**\n\n"
            "¿Estás seguro de que deseas continuar?\n\n"
            "Esta acción puede tener consecuencias permanentes."
        )

        CANCEL_CONFIRM = (
            "❌ **Cancelar Operación**\n\n"
            "¿Estás seguro de que deseas cancelar?\n\n"
            "Los cambios no guardados se perderán."
        )

    # ============================================
    # LOADING
    # ============================================

    class Loading:
        """Loading messages."""

        PROCESSING = "⏳ Procesando solicitud..."
        LOADING = "⏳ Cargando información..."
        SAVING = "💾 Guardando cambios..."
        CONNECTING = "🌐 Conectando con el servidor..."
        SEARCHING = "🔍 Buscando información..."
        VALIDATING = "✅ Validando datos..."

    # ============================================
    # EMPTY STATES
    # ============================================

    class Empty:
        """Empty state messages."""

        NO_DATA = (
            "📭 **Sin Datos**\n\n" "No hay información disponible en este momento."
        )

        NO_RESULTS = (
            "🔍 **Sin Resultados**\n\n" "No se encontraron resultados para tu búsqueda."
        )

        NO_ITEMS = (
            "📦 **Sin Elementos**\n\n" "No hay elementos para mostrar en esta sección."
        )

        NO_HISTORY = (
            "📋 **Sin Historial**\n\n" "No hay actividad reciente para mostrar."
        )

    # ============================================
    # MENU
    # ============================================

    class Menu:
        """Menu messages."""

        WELCOME_BACK = (
            "🏠 **Menú Principal**\n\n"
            "Has regresado al menú principal.\n\n"
            "Selecciona una opción para continuar:"
        )

    # ============================================
    # HELP
    # ============================================

    class Help:
        """Help messages."""

        GENERAL_HELP = (
            "❓ **Ayuda General**\n\n"
            "Usa los botones del menú para navegar.\n\n"
            "🔙 **Volver** - Regresa al menú anterior\n"
            "❌ **Cancelar** - Cancela la operación actual\n"
            "✅ **Confirmar** - Confirma la acción\n\n"
            "Si necesitas ayuda adicional, contacta soporte."
        )

        CONTACT_SUPPORT = (
            "🎧 **Contactar Soporte**\n\n"
            "Si tienes problemas o preguntas:\n\n"
            "📧 Envía un mensaje a soporte\n"
            "🌐 Usa el comando /support\n"
            "📞 Revisa nuestra documentación\n\n"
            "Estamos aquí para ayudarte."
        )
