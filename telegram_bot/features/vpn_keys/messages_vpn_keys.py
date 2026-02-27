"""
Mensajes para gestión de llaves VPN de uSipipo.

Author: uSipipo Team
Version: 3.2.0 - MarkdownV2 Compatible
"""


class VpnKeysMessages:
    """Mensajes para gestión de llaves VPN - MarkdownV2 Compatible."""

    # ============================================
    # CREATION FLOW - MarkdownV2 OK
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
    # ERRORS - MarkdownV2 OK
    # ============================================

    class Error:
        """Mensajes de error - MarkdownV2 Compatible."""

        CREATION_FAILED = (
            "💥 *ERROR AL CREAR*\n\n"
            "🚨 Fallo generando\n\n"
            "📟 `{error}`\n\n"
            "🔄 Intenta luego 📡"
        )

        KEY_LIMIT_REACHED = (
            "⚠️ *LÍMITE ALCANZADO*\n\n"
            "🔒 Máx: `{max_keys}` llaves\n\n"
            "💡 🗑️ Elimina o ⬆️ Sube plan ⚡"
        )

        INVALID_NAME = (
            "⛔ *NOMBRE INVÁLIDO*\n\n"
            "📝 Solo letras, números\n"
            "   y espacios 🎯"
        )

    # ============================================
    # SUCCESS - MarkdownV2 OK
    # ============================================

    class Success:
        """Mensajes de éxito - MarkdownV2 Compatible."""

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
            "📡 `{type}` \| 🔑 `{name}`\n"
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
