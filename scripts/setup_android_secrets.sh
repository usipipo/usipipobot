#!/bin/bash
# =============================================================================
# Setup Android APK Signing Secrets for GitHub Actions
# =============================================================================
# Este script configura los secrets necesarios para firmar la APK de Android
# en el pipeline de CI/CD de GitHub Actions.
#
# Requisitos:
#   - gh CLI instalado y autenticado
#   - Tener un keystore de Android (o generar uno nuevo)
#
# Uso:
#   ./scripts/setup_android_secrets.sh
# =============================================================================

set -e

REPO="usipipo/usipipobot"
KEYSTORE_FILE="android_app/release.keystore"
KEYSTORE_PASSWORD=""
KEY_ALIAS=""
KEY_PASSWORD=""

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
echo ""

# ===========================================================================
# OPCIÓN 1: Generar nuevo keystore
# ===========================================================================
echo "¿Deseas generar un NUEVO keystore o usar uno EXISTENTE?"
echo "  1) Generar nuevo keystore (recomendado para primer release)"
echo "  2) Usar keystore existente"
echo ""
read -p "Selecciona una opción [1/2]: " option

if [ "$option" == "1" ]; then
    echo ""
    echo "============================================================================="
    echo "  Generando Nuevo Keystore"
    echo "============================================================================="
    echo ""
    
    # Parámetros del keystore
    read -p "Keystore password (mínimo 6 caracteres): " -s KEYSTORE_PASSWORD
    echo ""
    read -p "Key alias (ej: usipipo): " KEY_ALIAS
    read -p "Key password (mínimo 6 caracteres): " -s KEY_PASSWORD
    echo ""
    read -p "Tu nombre (CN): " CN
    read -p "Tu organización (OU): " OU
    read -p "Ciudad (L): " L
    
    # Validar que el directorio existe
    mkdir -p android_app
    
    # Generar keystore
    echo ""
    echo "Generando keystore en: $KEYSTORE_FILE"
    keytool -genkey -v \
        -keystore "$KEYSTORE_FILE" \
        -alias "$KEY_ALIAS" \
        -keyalg RSA \
        -keysize 2048 \
        -validity 10000 \
        -storepass "$KEYSTORE_PASSWORD" \
        -keypass "$KEY_PASSWORD" \
        -dname "CN=$CN, OU=$OU, L=$L, S=Unknown, C=Unknown"
    
    echo "✅ Keystore generado exitosamente"
    
elif [ "$option" == "2" ]; then
    echo ""
    echo "============================================================================="
    echo "  Usar Keystore Existente"
    echo "============================================================================="
    echo ""
    
    read -p "Ruta al keystore existente: " KEYSTORE_FILE
    read -p "Keystore password: " -s KEYSTORE_PASSWORD
    echo ""
    read -p "Key alias: " KEY_ALIAS
    echo ""
    read -p "Key password: " -s KEY_PASSWORD
    echo ""
    
    # Verificar que el keystore existe
    if [ ! -f "$KEYSTORE_FILE" ]; then
        echo "❌ El archivo keystore no existe: $KEYSTORE_FILE"
        exit 1
    fi
    
    echo "✅ Keystore encontrado: $KEYSTORE_FILE"
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

# Codificar keystore en base64
echo "Codificando keystore en base64..."
KEYSTORE_B64=$(base64 -w 0 "$KEYSTORE_FILE")
echo "✅ Keystore codificado (${#KEYSTORE_B64} caracteres)"
echo ""

# Configurar secrets
echo "Configurando secrets en $REPO..."
echo ""

# Secret 1: ANDROID_KEYSTORE_B64
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
echo "Próximos pasos:"
echo "  1. Verificar secrets en: https://github.com/$REPO/settings/secrets/actions"
echo "  2. Hacer push de cambios para trigger el workflow"
echo "  3. O ejecutar manualmente: gh workflow run android-ci.yml"
echo ""
echo "⚠️  IMPORTANTE: Guarda una copia de seguridad del keystore en un lugar seguro."
echo "    Si pierdes el keystore, NO podrás actualizar tu APK en Google Play."
echo ""

# Guardar información del keystore (sin passwords)
cat > android_app/keystore_info.txt << EOF
===============================================================================
Keystore Information
===============================================================================
File: $KEYSTORE_FILE
Alias: $KEY_ALIAS
Validity: 10000 days (~27 years)
Generated: $(date)

IMPORTANT: Store this keystore file securely!
If you lose this file, you won't be able to publish updates to your app.

Backup Recommendations:
  - Store in a password manager
  - Keep a copy in an encrypted USB drive
  - Add to team secure storage if working in a team
===============================================================================
EOF

echo "📄 Información guardada en: android_app/keystore_info.txt"
echo ""
