"""
Estilos y configuraciones para el sistema de Spinner.

Este módulo contiene las constantes de estilos, frames de animación
y mensajes predefinidos para diferentes tipos de operaciones.
"""

from typing import Dict, List


class SpinnerStyles:
    """Estilos y configuraciones visuales para spinners."""

    # Emojis para animación de spinner (estilo braille)
    SPINNER_FRAMES: List[str] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    # Mensajes predefinidos para diferentes tipos de operaciones
    MESSAGES: Dict[str, str] = {
        "loading": "🔄 Cargando...",
        "processing": "⚙️ Procesando...",
        "connecting": "🔌 Conectando...",
        "creating": "🔨 Creando...",
        "updating": "📝 Actualizando...",
        "deleting": "🗑️ Eliminando...",
        "searching": "🔍 Buscando...",
        "validating": "✅ Validando...",
        "database": "💾 Accediendo a la base de datos...",
        "vpn": "🌐 Configurando VPN...",
        "payment": "💳 Procesando pago...",
        "register": "👤 Registrando usuario...",
        "ai_thinking": "🌊 Sip está pensando...",
        "ai_searching": "🌊 Sip está buscando información...",
        "ai_analyzing": "🌊 Sip está analizando tu problema...",
        "ai_generating": "🌊 Sip está generando respuesta...",
        "default": "⏳ Procesando solicitud...",
    }
