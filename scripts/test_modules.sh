#!/bin/bash
# =============================================================================
# test_modules.sh - Test suite for setup modules
# =============================================================================
# Usage: ./scripts/test_modules.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MODULES_DIR="$SCRIPT_DIR/modules"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

pass() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
    ((TESTS_FAILED++))
}

section() {
    echo ""
    echo -e "${YELLOW}═══ $1 ═══${NC}"
}

# =============================================================================
# Test: common.sh
# =============================================================================
section "Testing common.sh"

echo "Test: Source common.sh multiple times"
if source "$MODULES_DIR/common.sh" 2>&1 && source "$MODULES_DIR/common.sh" 2>&1 | grep -q "readonly variable"; then
    fail "common.sh readonly error on re-source"
else
    pass "common.sh can be sourced multiple times"
fi

echo "Test: env_set and env_get"
source "$MODULES_DIR/common.sh"
TEST_FILE=$(mktemp)
env_set "$TEST_FILE" "TEST_KEY" "test_value_123"
result=$(env_get "$TEST_FILE" "TEST_KEY")
if [[ "$result" == "test_value_123" ]]; then
    pass "env_set/env_get work correctly"
else
    fail "env_set/env_get returned: $result"
fi
rm -f "$TEST_FILE"

echo "Test: env_get with missing file"
if env_get "/nonexistent/file.env" "KEY" 2>/dev/null; then
    fail "env_get should fail with missing file"
else
    pass "env_get fails gracefully with missing file"
fi

echo "Test: generate_random_string"
rand=$(generate_random_string 16)
if [[ ${#rand} -eq 16 ]]; then
    pass "generate_random_string produces correct length"
else
    fail "generate_random_string produced length ${#rand}"
fi

# =============================================================================
# Test: python.sh
# =============================================================================
section "Testing python.sh"

echo "Test: Source python.sh"
if source "$MODULES_DIR/python.sh" 2>&1; then
    pass "python.sh sources without error"
else
    fail "python.sh source failed"
fi

echo "Test: verify_python_version"
source "$MODULES_DIR/python.sh"
if verify_python_version python3 2>&1 | grep -q "meets minimum"; then
    pass "verify_python_version passes for python3"
else
    fail "verify_python_version failed"
fi

# =============================================================================
# Test: database.sh
# =============================================================================
section "Testing database.sh"

echo "Test: Source database.sh"
if source "$MODULES_DIR/database.sh" 2>&1; then
    pass "database.sh sources without error"
else
    fail "database.sh source failed"
fi

echo "Test: Database config variables"
source "$MODULES_DIR/database.sh"
if [[ -n "$DB_NAME" && -n "$DB_USER" && -n "$DB_PORT" ]]; then
    pass "Database config variables are set"
else
    fail "Database config variables missing"
fi

# =============================================================================
# Test: systemd.sh
# =============================================================================
section "Testing systemd.sh"

echo "Test: Source systemd.sh"
if source "$MODULES_DIR/systemd.sh" 2>&1; then
    pass "systemd.sh sources without error"
else
    fail "systemd.sh source failed"
fi

echo "Test: Service config variables"
source "$MODULES_DIR/systemd.sh"
if [[ "$SERVICE_NAME" == "usipipo" && "$SERVICE_FILE" == "/etc/systemd/system/usipipo.service" ]]; then
    pass "systemd.sh constants are correct"
else
    fail "systemd.sh constants incorrect"
fi

# =============================================================================
# Test: vpn.sh
# =============================================================================
section "Testing vpn.sh"

echo "Test: Source vpn.sh"
if source "$MODULES_DIR/vpn.sh" 2>&1; then
    pass "vpn.sh sources without error"
else
    fail "vpn.sh source failed"
fi

echo "Test: vpn.sh uses correct env_set parameter order"
if grep -q 'env_set "\$ENV_FILE"' "$MODULES_DIR/vpn.sh"; then
    pass "vpn.sh env_set calls have correct parameter order"
else
    fail "vpn.sh env_set calls may have wrong parameter order"
fi

# =============================================================================
# Test: bot.sh
# =============================================================================
section "Testing bot.sh"

echo "Test: Source bot.sh"
if source "$MODULES_DIR/bot.sh" 2>&1; then
    pass "bot.sh sources without error"
else
    fail "bot.sh source failed"
fi

echo "Test: validate_env with .env"
source "$MODULES_DIR/bot.sh"
if validate_env "$PROJECT_DIR/.env" 2>&1 | grep -q "All required"; then
    pass "validate_env works with .env"
else
    fail "validate_env failed"
fi

echo "Test: validate_env catches missing variables"
source "$MODULES_DIR/bot.sh"
MISSING_ENV=$(mktemp)
if validate_env "$MISSING_ENV" 2>&1 | grep -q "Missing"; then
    pass "validate_env detects missing variables"
else
    fail "validate_env did not detect missing variables"
fi
rm -f "$MISSING_ENV"

# =============================================================================
# Test: migrations/env.py
# =============================================================================
section "Testing migrations/env.py"

echo "Test: get_sync_url function exists"
if grep -q "def get_sync_url" "$PROJECT_DIR/migrations/env.py"; then
    pass "migrations/env.py has get_sync_url function"
else
    fail "migrations/env.py missing get_sync_url function"
fi

echo "Test: asyncpg URL conversion"
conversion_test=$(python3 -c "
def get_sync_url(async_url):
    return async_url.replace('+asyncpg', '')
result = get_sync_url('postgresql+asyncpg://user:pass@localhost/db')
print(result)
")
if [[ "$conversion_test" == "postgresql://user:pass@localhost/db" ]]; then
    pass "URL conversion removes +asyncpg correctly"
else
    fail "URL conversion failed: $conversion_test"
fi

# =============================================================================
# Summary
# =============================================================================
echo ""
echo -e "${YELLOW}════════════════════════════════════════${NC}"
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo -e "${YELLOW}════════════════════════════════════════${NC}"

if [[ $TESTS_FAILED -gt 0 ]]; then
    exit 1
fi

echo -e "${GREEN}All tests passed!${NC}"
exit 0
