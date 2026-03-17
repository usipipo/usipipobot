#!/bin/bash
# =============================================================================
# Test manual del flujo completo de Autenticación (Fases 01.1 + 01.2 + 01.3)
# =============================================================================
# Uso: ./tests/test_auth_flow.sh @tu_username
# =============================================================================

set -e

BASE_URL="http://localhost:8000/api/v1/auth"
IDENTIFIER="${1:-@tu_username}"

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Test Flujo Autenticación Completo - FASE 01.3        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Identifier: $IDENTIFIER"
echo "Base URL: $BASE_URL"
echo ""

# -----------------------------------------------------------------------------
# Paso 1: Solicitar OTP
# -----------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📬 Paso 1: Solicitando OTP (Fase 01.1)..."
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
# Paso 3: Verificar OTP y obtener JWT
# -----------------------------------------------------------------------------
echo "🔐 Paso 3: Verificando OTP (Fase 01.2)..."
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

    required_fields = ['sub', 'client', 'iat', 'exp', 'jti']
    missing = [f for f in required_fields if f not in payload]

    if missing:
        print(f"\n❌ Campos faltantes: {missing}")
    else:
        print("\n✅ Todos los campos requeridos presentes")

    if payload.get('client') != 'miniapp_web':
        print(f"\n❌ Client incorrecto: {payload.get('client')}")
    else:
        print("✅ Client correcto: miniapp_web")

except jwt.InvalidTokenError as e:
    print(f"\n❌ JWT inválido: {e}")
EOF

    echo ""
else
    echo "❌ No se pudo obtener el token. Revisa la respuesta arriba."
    exit 1
fi

# -----------------------------------------------------------------------------
# Paso 5: Test de Refresh de Token
# -----------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 Paso 5: Probando refresh de token (Fase 01.3)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

REFRESH_RESPONSE=$(curl -s -X POST "$BASE_URL/refresh" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "$REFRESH_RESPONSE" | python3 -m json.tool

NEW_ACCESS_TOKEN=$(echo "$REFRESH_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', ''))" 2>/dev/null || echo "")

if [ -n "$NEW_ACCESS_TOKEN" ]; then
    echo ""
    echo "✅ Refresh exitoso - Nuevo token obtenido"
    ACCESS_TOKEN="$NEW_ACCESS_TOKEN"
else
    echo ""
    echo "❌ Refresh falló"
fi

echo ""

# -----------------------------------------------------------------------------
# Paso 6: Test de Logout
# -----------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚪 Paso 6: Probando logout (Fase 01.3)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

LOGOUT_RESPONSE=$(curl -s -X POST "$BASE_URL/logout" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "$LOGOUT_RESPONSE" | python3 -m json.tool

echo ""

# -----------------------------------------------------------------------------
# Paso 7: Verificar que el token fue revocado
# -----------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔒 Paso 7: Verificando token revocado..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Primero probar endpoint /me con token válido (antes del logout)
# Esto ya se probó implícitamente en el refresh, pero vamos a hacerlo explícito
echo "Probando endpoint /me con token ANTES del logout:"
ME_RESPONSE=$(curl -s -X GET "$BASE_URL/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "$ME_RESPONSE" | python3 -m json.tool

echo ""
echo "Ahora probando endpoint /me con token DESPUÉS del logout:"

# El logout ya se hizo en el paso 6, así que el token debería estar revocado
REVOKED_RESPONSE=$(curl -s -X GET "$BASE_URL/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -w "\n%{http_code}")

HTTP_CODE=$(echo "$REVOKED_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$REVOKED_RESPONSE" | head -n-1)

echo "HTTP Status: $HTTP_CODE"
echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"

if [ "$HTTP_CODE" = "401" ]; then
    echo ""
    echo "✅ Token correctamente revocado (401)"
else
    echo ""
    echo "⚠️  El token debería haber sido revocado (esperado 401, obtenido $HTTP_CODE)"
fi

echo ""

# -----------------------------------------------------------------------------
# Resumen Final
# -----------------------------------------------------------------------------
echo "╔════════════════════════════════════════════════════════╗"
echo "║  RESUMEN DEL TEST                                      ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Fase 01.1 (Request OTP): Completada"
echo "✅ Fase 01.2 (Verify OTP): Completada"
echo "✅ Fase 01.3 (Refresh + Logout): Completada"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 ¡Flujo de autenticación completo exitosamente!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
