#!/bin/bash
# =============================================================================
# Setup Android APK Signing Secrets for GitHub Actions (Manual Mode)
# =============================================================================
# Este script configura los secrets necesarios para firmar la APK de Android
# sin requerir Java/keytool localmente.
#
# Opciones:
#   1. Configurar secrets manualmente (ingresando valores)
#   2. Usar valores placeholder para testing (sin firma real)
#
# Requisitos:
#   - gh CLI instalado y autenticado
#
# Uso:
#   ./scripts/setup_android_secrets_manual.sh
# =============================================================================

set -e

REPO="usipipo/usipipobot"

echo "============================================================================="
echo "  Setup Android APK Signing Secrets for GitHub Actions"
echo "============================================================================="
echo ""

# Verificar gh CLI
if ! command -v gh &> /dev/null; then
    echo "❌ gh CLI no está instalado. Instalar con: sudo apt install gh"
    exit 1
fi

# Verificar autenticación
if ! gh auth status &> /dev/null; then
    echo "❌ gh CLI no está autenticado. Ejecutar: gh auth login"
    exit 1
fi

echo "✅ gh CLI autenticado correctamente"
echo "   Repositorio: $REPO"
echo ""

# ===========================================================================
# Selección de modo
# ===========================================================================
echo "Selecciona el modo de configuración:"
echo ""
echo "  1) 📝 Configurar secrets manualmente (recomendado para producción)"
echo "     - Ingresa tu propio keystore (base64)"
echo "     - Ingresa passwords y alias"
echo ""
echo "  2) 🧪 Usar valores placeholder (solo testing/CI)"
echo "     - La APK se compilará sin firmar o con firma debug"
echo "     - No usar para releases en producción"
echo ""
read -p "Selecciona una opción [1/2]: " option

if [ "$option" == "1" ]; then
    echo ""
    echo "============================================================================="
    echo "  Configuración Manual de Secrets"
    echo "============================================================================="
    echo ""
    echo "Para obtener el keystore en base64, ejecuta en tu máquina local:"
    echo "  base64 -w 0 tu_keystore.jks"
    echo ""
    
    read -p "Keystore en base64 (pegar valor completo): " KEYSTORE_B64
    read -p "Keystore password: " -s KEYSTORE_PASSWORD
    echo ""
    read -p "Key alias: " KEY_ALIAS
    echo ""
    read -p "Key password: " -s KEY_PASSWORD
    echo ""
    
    # Validar que se ingresaron valores
    if [ -z "$KEYSTORE_B64" ]; then
        echo "❌ Debes ingresar el keystore en base64"
        exit 1
    fi
    
elif [ "$option" == "2" ]; then
    echo ""
    echo "============================================================================="
    echo "  Configuración Placeholder (Testing)"
    echo "============================================================================="
    echo ""
    echo "⚠️  ADVERTENCIA: La APK se compilará SIN FIRMA VÁLIDA"
    echo "    - Solo usar para testing en CI"
    echo "    - NO usar para releases en Google Play"
    echo ""
    read -p "¿Continuar con valores placeholder? [y/N]: " confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Operación cancelada."
        exit 0
    fi
    
    # Valores placeholder
    KEYSTORE_B64="UExBQ0VIT0xERVJfS0VZU1RPUkVfQkFTRTY0X05FRURTX1JFQUxfS0VZU1RPUkU="
    KEYSTORE_PASSWORD="placeholder_password"
    KEY_ALIAS="placeholder_alias"
    KEY_PASSWORD="placeholder_key_password"
    
    echo ""
    echo "Usando valores placeholder..."
else
    echo "❌ Opción inválida"
    exit 1
fi

# ===========================================================================
# Configurar secrets en GitHub
# ===========================================================================
echo ""
echo "============================================================================="
echo "  Configurando Secrets en GitHub Actions"
echo "============================================================================="
echo ""

# Configurar secrets
echo "  [1/4] ANDROID_KEYSTORE_B64"
gh secret set ANDROID_KEYSTORE_B64 \
    --body "$KEYSTORE_B64" \
    --repo "$REPO" && echo "      ✅ Configurado" || echo "      ❌ Error"

# Secret 2: ANDROID_KEYSTORE_PASSWORD
echo "  [2/4] ANDROID_KEYSTORE_PASSWORD"
gh secret set ANDROID_KEYSTORE_PASSWORD \
    --body "$KEYSTORE_PASSWORD" \
    --repo "$REPO" && echo "      ✅ Configurado" || echo "      ❌ Error"

# Secret 3: ANDROID_KEY_ALIAS
echo "  [3/4] ANDROID_KEY_ALIAS"
gh secret set ANDROID_KEY_ALIAS \
    --body "$KEY_ALIAS" \
    --repo "$REPO" && echo "      ✅ Configurado" || echo "      ❌ Error"

# Secret 4: ANDROID_KEY_PASSWORD
echo "  [4/4] ANDROID_KEY_PASSWORD"
gh secret set ANDROID_KEY_PASSWORD \
    --body "$KEY_PASSWORD" \
    --repo "$REPO" && echo "      ✅ Configurado" || echo "      ❌ Error"

echo ""
echo "============================================================================="
echo "  ✅ Secrets Configurados Exitosamente"
echo "============================================================================="
echo ""
echo "Secrets configurados en $REPO:"
echo "  - ANDROID_KEYSTORE_B64"
echo "  - ANDROID_KEYSTORE_PASSWORD"
echo "  - ANDROID_KEY_ALIAS"
echo "  - ANDROID_KEY_PASSWORD"
echo ""
echo "Verificar en: https://github.com/$REPO/settings/secrets/actions"
echo ""
echo "============================================================================="
echo "  Próximos Pasos"
echo "============================================================================="
echo ""
echo "1. Para releases en PRODUCCIÓN:"
echo "   - Genera un keystore real con keytool (requiere Java)"
echo "   - Ejecuta este script nuevamente con opción 1"
echo "   - Guarda el keystore en un lugar SEGURO (no se puede recuperar)"
echo ""
echo "2. Para TESTING en CI:"
echo "   - Los secrets ya están configurados"
echo "   - El workflow build-debug funcionará"
echo "   - El workflow build-release creará APK sin firmar válida"
echo ""
echo "3. Comandos útiles:"
echo "   gh workflow run android-ci.yml                    # Trigger manual"
echo "   gh run list --workflow android-ci.yml             # Ver runs"
echo "   gh run watch <run-id>                             # Ver progreso"
echo ""
