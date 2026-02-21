# Testing System Design - Issue #82

## Overview

Create comprehensive unit tests for the simplified uSipipo VPN Bot system to achieve >80% code coverage.

## Current State

- **31 tests passing** across existing test files
- Tests exist for: DataPackageService, DataPackageRepository, VpnKeyFlow (basic), PackageExpirationJob
- Missing tests for: VpnService, PaymentService, AdminService, UserRepository, KeyRepository

## Testing Strategy

### Approach: Complete with Mocks

All tests will use mocks to isolate units from external dependencies:
- No database connections
- No real API calls to Outline/WireGuard servers
- No Telegram API calls
- Fast execution, deterministic results

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures
├── application/services/
│   ├── test_data_package_service.py     # ✓ Exists (14 tests)
│   ├── test_vpn_service.py              # NEW
│   ├── test_payment_service.py          # NEW
│   └── test_admin_service.py            # NEW
├── domain/entities/
│   └── test_data_package.py             # ✓ Exists (1 test)
├── infrastructure/persistence/
│   ├── test_data_package_repository.py  # ✓ Exists (10 tests)
│   ├── test_user_repository.py          # NEW
│   └── test_key_repository.py           # NEW
├── infrastructure/jobs/
│   └── test_package_expiration_job.py   # ✓ Exists (2 tests)
├── integration/
│   └── test_vpn_key_flow.py             # ✓ Exists (3 tests)
└── telegram_bot/features/vpn_keys/
    └── test_handlers_vpn_keys.py        # ✓ Exists (1 test)
```

## New Test Files

### 1. test_vpn_service.py

Tests for VpnService methods:
- `create_key` - Outline and WireGuard key creation
- `create_key` - Error when key limit reached
- `create_key` - Auto-create user if not exists
- `revoke_key` - Success case
- `revoke_key` - Key not found
- `revoke_key` - User cannot delete (no deposit)
- `get_user_status` - Returns correct summary
- `fetch_real_usage` - Outline metrics
- `fetch_real_usage` - WireGuard metrics
- `rename_key` - Success and error cases
- `get_server_status` - Outline and WireGuard
- `can_user_create_key` - Limit checks
- `upgrade_to_vip` - User upgrade flow

### 2. test_payment_service.py

Tests for PaymentService methods:
- `update_balance` - Deposit increases balance
- `update_balance` - Records transaction
- `deduct_balance` - Success case
- `deduct_balance` - Insufficient balance error
- `apply_referral_commission` - 10% commission calculation
- `activate_vip` - Sets VIP expiry
- `add_storage` - Increases storage
- `get_user_balance` - Returns correct balance

### 3. test_admin_service.py

Tests for AdminService methods:
- `get_dashboard_stats` - Aggregates statistics
- `get_all_users` - Returns user list
- `get_user_keys` - Returns keys for user
- `delete_key_from_servers` - WireGuard and Outline
- `delete_key_from_db` - Success and error
- `delete_user_key_complete` - Full deletion flow
- `get_server_status` - Both servers healthy/unhealthy
- `update_user_status` - Valid status transitions
- `assign_role_to_user` - Role assignment
- `block_user` / `unblock_user`

### 4. test_user_repository.py

Tests for PostgresUserRepository:
- `save` - New user creation
- `save` - Update existing user
- `get_by_id` - Found and not found
- `exists` - True and false cases
- `get_by_referral_code` - Found and not found
- `update_balance` - Success case
- `get_referrals` - Returns referral list
- `create_user` - Auto-generates referral code

### 5. test_key_repository.py

Tests for PostgresKeyRepository:
- `save` - New key creation
- `save` - Update existing key
- `get_by_user_id` - Returns user's keys
- `get_all_active` - Returns only active keys
- `get_by_id` - Found and not found
- `delete` - Soft delete (sets is_active=False)
- `update_usage` - Updates used_bytes
- `reset_data_usage` - Resets to zero
- `get_keys_needing_reset` - Filters by billing date

## Shared Fixtures (conftest.py)

```python
@pytest.fixture
def mock_session():
    """Mock AsyncSession for database operations."""
    
@pytest.fixture
def mock_user_repo():
    """Mock IUserRepository."""
    
@pytest.fixture
def mock_key_repo():
    """Mock IKeyRepository."""
    
@pytest.fixture
def mock_package_repo():
    """Mock IDataPackageRepository."""
    
@pytest.fixture
def mock_outline_client():
    """Mock OutlineClient."""
    
@pytest.fixture
def mock_wireguard_client():
    """Mock WireGuardClient."""
    
@pytest.fixture
def sample_user():
    """Sample User entity for tests."""
    
@pytest.fixture
def sample_vpn_key():
    """Sample VpnKey entity for tests."""
    
@pytest.fixture
def sample_data_package():
    """Sample DataPackage entity for tests."""
```

## Expected Test Count

| File | Tests |
|------|-------|
| test_vpn_service.py | ~15 |
| test_payment_service.py | ~10 |
| test_admin_service.py | ~12 |
| test_user_repository.py | ~10 |
| test_key_repository.py | ~10 |
| **Total new** | **~57** |
| **Existing** | **31** |
| **Grand total** | **~88 tests** |

## Success Criteria

- [ ] All 88+ tests pass
- [ ] >80% code coverage on:
  - application/services/
  - domain/entities/
  - infrastructure/persistence/postgresql/
- [ ] No real external API calls in tests
- [ ] All tests complete in <10 seconds
