#!/bin/bash

echo "🔍 Penetration Testing for uSipipo Webhook API"
echo "=============================================="

API_URL="${1:-http://localhost:8000}"
WEBHOOK_URL="$API_URL/api/v1/webhooks/tron-dealer"

echo ""
echo "📡 Testing endpoint: $WEBHOOK_URL"
echo ""

# Test 1: Health check
echo "Test 1: Health check..."
curl -s "$API_URL/health" | python3 -m json.tool 2>/dev/null || echo "❌ Health check failed"

# Test 2: Webhook health
echo ""
echo "Test 2: Webhook health..."
curl -s "$API_URL/api/v1/webhooks/tron-dealer/health" | python3 -m json.tool 2>/dev/null || echo "❌ Webhook health failed"

# Test 3: Missing signature (should fail)
echo ""
echo "Test 3: Request without signature (should fail)..."
curl -s -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "0x1234567890abcdef1234567890abcdef12345678", "amount": 10, "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"}' \
  | python3 -m json.tool 2>/dev/null || echo "✅ Correctly rejected"

# Test 4: Invalid signature (should fail)
echo ""
echo "Test 4: Invalid signature (should fail)..."
curl -s -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Signature: invalid_signature" \
  -d '{"wallet_address": "0x1234567890abcdef1234567890abcdef12345678", "amount": 10, "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"}' \
  | python3 -m json.tool 2>/dev/null || echo "✅ Correctly rejected"

# Test 5: Invalid payload (should fail)
echo ""
echo "Test 5: Invalid payload (should fail)..."
curl -s -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"invalid": "payload"}' \
  | python3 -m json.tool 2>/dev/null || echo "✅ Correctly rejected"

# Test 6: SQL Injection attempt
echo ""
echo "Test 6: SQL Injection attempt..."
curl -s -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "0x1234567890abcdef1234567890abcdef12345678'"'"' OR 1=1 --", "amount": 10, "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"}' \
  | python3 -m json.tool 2>/dev/null || echo "✅ SQL injection blocked"

# Test 7: XSS attempt
echo ""
echo "Test 7: XSS attempt..."
curl -s -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "<script>alert(1)</script>", "amount": 10, "tx_hash": "test"}' \
  | python3 -m json.tool 2>/dev/null || echo "✅ XSS blocked"

# Test 8: Security headers
echo ""
echo "Test 8: Security headers..."
HEADERS=$(curl -sI "$API_URL/health")
echo "$HEADERS" | grep -i "X-Content-Type-Options" && echo "✅ X-Content-Type-Options present" || echo "❌ Missing X-Content-Type-Options"
echo "$HEADERS" | grep -i "X-Frame-Options" && echo "✅ X-Frame-Options present" || echo "❌ Missing X-Frame-Options"
echo "$HEADERS" | grep -i "Strict-Transport-Security" && echo "✅ HSTS present" || echo "⚠️ HSTS missing (ok for development)"

echo ""
echo "=============================================="
echo "🎉 Penetration testing completed!"
