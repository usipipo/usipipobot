"""
Mensajes para gestión de llaves VPN de uSipipo.

Author: uSipipo Team
Version: 3.3.0 - Markdown Standardized
"""


class VpnKeysMessages:
    """Mensajes para gestión de llaves VPN."""

    # ============================================
    # CREATION FLOW
    # ============================================

    SELECT_TYPE = (
        "🔮 ╔══════════════╗\n"
        "    ║ 🛡️ ELIGE VPN ║\n"
        "    ╚══════════════╝\n\n"
        "💡 *Según dispositivo:*\n"
        "   • 🌐 *Outline*\n"
        "   • 🔒 *WireGuard*"
    )

    CANCELLED = (
        "❌ *CANCELADO*"
    )

    # ============================================
    # ERRORS
    # ============================================

    class Error:
        """Mensajes de error."""

        CREATION_FAILED = (
            "💥 *ERROR AL CREAR*\n\n"
            "🚨 Fallo generando\n\n"
            "📟 `{error}`\n\n"
            "🔄 Intenta luego 📡"
        )

        KEY_LIMIT_REACHED = (
            "⚠️ *LÍMITE ALCANZADO*\n\n"
            "🔒 Has usado `{used_keys}`/`{max_keys}` claves\n\n"
            "💡 Para crear más claves, compra slots adicionales\n"
            "   Cada slot te permite crear 1 clave extra"
        )

        INVALID_NAME = (
            "⛔ *NOMBRE INVÁLIDO*\n\n"
            "📝 Solo letras, números\n"
            "   y espacios 🎯"
        )

    # ============================================
    # SUCCESS
    # ============================================

    class Success:
        """Mensajes de éxito."""

        KEY_CREATED = (
            "🔮 ╔══════════════╗\n"
            "    ║ ✅ CREADA    ║\n"
            "    ╚══════════════╝\n\n"
            "📡 `{type}`\n\n"
            "🚀 Activa y lista ⚡"
        )

        KEY_CREATED_WITH_DATA = (
            "🔮 ╔══════════════╗\n"
            "    ║ ✅ CREADA    ║\n"
            "    ╚══════════════╝\n\n"
            "📡 `{type}` | 🔑 `{name}`\n"
            "💾 `{data_limit:.1f}GB`\n\n"
            "🚀 Lista para usar ⚡"
        )

        KEY_DELETED = (
            "🗑️ *ELIMINADA*\n\n"
            "💥 `{name}` destruida\n\n"
            "🔌 Devices off ⚡"
        )

        KEY_RENAMED = (
            "✏️ *RENOMBRADA*\n\n"
            "✨ {new_name}\n\n"
            "✅ Listo 🎯"
        )
