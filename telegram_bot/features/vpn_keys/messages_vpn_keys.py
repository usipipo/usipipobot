"""
Mensajes para gestión de llaves VPN de uSipipo.

Author: uSipipo Team
Version: 2.0.0 - Feature-based architecture
"""


class VpnKeysMessages:
    """Mensajes para gestión de llaves VPN."""
    
    # ============================================
    # CREATION FLOW
    # ============================================
    
    SELECT_TYPE = (
        "🛡️ **Selecciona tu protocolo**\n\n"
        "Elige según tu dispositivo y necesidad:"
    )
    
    CANCELLED = "❌ Operación cancelada."
    
    # ============================================
    # ERRORS
    # ============================================
    
    class Error:
        """Mensajes de error."""
        
        CREATION_FAILED = (
            "❌ **Error creando llave**\n\n"
            "No pude generar tu llave VPN. Error: {error}\n\n"
            "Por favor, intenta más tarde o contacta soporte."
        )
        
        KEY_LIMIT_REACHED = (
            "❌ **Límite de llaves alcanzado**\n\n"
            "Has alcanzado el límite de **{max_keys}** llaves para tu plan.\n\n"
            "💡 *Soluciones:*\n"
            "• Elimina llaves que no usas desde **🛡️ Mis Llaves**\n"
            "• Actualiza tu plan para más llaves"
        )
        
        INVALID_NAME = (
            "❌ **Nombre inválido**\n\n"
            "El nombre de la llave solo puede contener letras, números y espacios.\n\n"
            "Por favor, intenta con otro nombre."
        )
    
    # ============================================
    # SUCCESS
    # ============================================
    
    class Success:
        """Mensajes de éxito."""
        
        KEY_CREATED = (
            "✅ **¡Llave creada exitosamente!**\n\n"
            "📡 Protocolo: **{type}**\n\n"
            "Sigue las instrucciones para conectarte."
        )
        
        KEY_CREATED_WITH_DATA = (
            "✅ **¡Llave creada exitosamente!**\n\n"
            "📡 **Protocolo:** {type}\n"
            "🔑 **Nombre:** {name}\n"
            "📊 **Datos disponibles:** {data_limit:.1f} GB\n\n"
            "Sigue las instrucciones para conectarte."
        )
        
        KEY_DELETED = (
            "🗑️ **Llave eliminada**\n\n"
            "La llave **{name}** ha sido eliminada permanentemente.\n\n"
            "Todos los dispositivos conectados se desconectarán."
        )
        
        KEY_RENAMED = (
            "✏️ **Llave renombrada**\n\n"
            "Tu llave ahora se llama: **{new_name}**"
        )
