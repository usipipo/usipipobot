#!/bin/bash
# =============================================================================
# Test manual del flujo completo OTP (Fase 01.2)
# =============================================================================
# Uso: ./scripts/test_otp_flow.sh @tu_username
# =============================================================================

set -e

BASE_URL="http://localhost:8000/api/v1/auth"
IDENTIFIER="${1:-@tu_username}"

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Test Flujo OTP Completo - Fase 01.2                  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Identifier: $IDENTIFIER"
echo "Base URL: $BASE_URL"
echo ""

# -----------------------------------------------------------------------------
# Paso 1: Solicitar OTP
# -----------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📬 Paso 1: Solicitando OTP..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

OTP_RESPONSE=$(curl -s -X POST "$BASE_URL/request-otp" \
  -H "Content-Type: application/json" \
  -d "{\"identifier\": \"$IDENTIFIER\"}")

echo "$OTP_RESPONSE" | python3 -m json.tool

echo ""
echo "✅ Revisa tu Telegram para obtener el código OTP"
echo ""

# -----------------------------------------------------------------------------
# Paso 2: Pedir código OTP al usuario
# -----------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
read -p "Ingresa el código OTP recibido: " OTP_CODE_RAW
# Remover espacios del OTP (Telegram lo envía como "699 987")
OTP_CODE=$(echo "$OTP_CODE_RAW" | tr -d ' ')
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# -----------------------------------------------------------------------------
# Paso 3: Verificar OTP
# -----------------------------------------------------------------------------
echo "🔐 Paso 3: Verificando OTP..."
echo ""

VERIFY_RESPONSE=$(curl -s -X POST "$BASE_URL/verify-otp" \
  -H "Content-Type: application/json" \
  -d "{\"identifier\": \"$IDENTIFIER\", \"otp\": \"$OTP_CODE\"}")

echo "$VERIFY_RESPONSE" | python3 -m json.tool

echo ""

# -----------------------------------------------------------------------------
# Paso 4: Extraer y verificar JWT
# -----------------------------------------------------------------------------
ACCESS_TOKEN=$(echo "$VERIFY_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', ''))" 2>/dev/null || echo "")

if [ -n "$ACCESS_TOKEN" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 Paso 4: Verificando estructura del JWT..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    python3 << EOF
import jwt
import json

token = "$ACCESS_TOKEN"

try:
    # Decodificar sin verificar firma (solo para testing)
    payload = jwt.decode(token, options={"verify_signature": False})

    print("✅ JWT válido (estructura)")
    print(f"   - sub (telegram_id): {payload.get('sub')}")
    print(f"   - client: {payload.get('client')}")

    from datetime import datetime
    iat = payload.get('iat')
    exp = payload.get('exp')
    if iat:
        print(f"   - iat (issued at): {datetime.fromtimestamp(iat)}")
    if exp:
        print(f"   - exp (expires): {datetime.fromtimestamp(exp)}")
    print(f"   - jti (JWT ID): {payload.get('jti')}")

    # Verificar campos requeridos
    required_fields = ['sub', 'client', 'iat', 'exp', 'jti']
    missing = [f for f in required_fields if f not in payload]

    if missing:
        print(f"\n❌ Campos faltantes: {missing}")
    else:
        print("\n✅ Todos los campos requeridos presentes")

    # Verificar client
    if payload.get('client') != 'miniapp_web':
        print(f"\n❌ Client incorrecto: {payload.get('client')}")
    else:
        print("✅ Client correcto: miniapp_web")

except jwt.InvalidTokenError as e:
    print(f"\n❌ JWT inválido: {e}")
EOF

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ ¡Flujo completado exitosamente!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "❌ No se pudo obtener el token. Revisa la respuesta arriba."
    exit 1
fi
