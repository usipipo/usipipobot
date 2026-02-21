# Testing System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create comprehensive unit tests for uSipipo VPN Bot to achieve >80% code coverage

**Architecture:** Test all services and repositories using mocks (AsyncMock, MagicMock). No real DB or API connections. Fixtures in conftest.py for reusability.

**Tech Stack:** pytest, pytest-asyncio, unittest.mock

---

## Task 1: Create Shared Fixtures in conftest.py

**Files:**
- Modify: `tests/conftest.py`

**Step 1: Write fixtures for mocks and sample entities**

```python
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from domain.entities.user import User, UserStatus, UserRole
from domain.entities.vpn_key import VpnKey, KeyType
from domain.entities.data_package import DataPackage, PackageType


@pytest.fixture
def mock_session():
    """Mock AsyncSession for database operations."""
    session = AsyncMock()
    session.get = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_user_repo():
    """Mock IUserRepository."""
    return AsyncMock()


@pytest.fixture
def mock_key_repo():
    """Mock IKeyRepository."""
    return AsyncMock()


@pytest.fixture
def mock_package_repo():
    """Mock IDataPackageRepository."""
    return AsyncMock()


@pytest.fixture
def mock_transaction_repo():
    """Mock ITransactionRepository."""
    return AsyncMock()


@pytest.fixture
def mock_outline_client():
    """Mock OutlineClient."""
    client = AsyncMock()
    client.create_key = AsyncMock(return_value={
        "id": "outline-key-123",
        "access_url": "ss://test@server:1234#TestKey",
    })
    client.delete_key = AsyncMock(return_value=True)
    client.get_metrics = AsyncMock(return_value={"outline-key-123": 1024})
    client.get_server_info = AsyncMock(return_value={"is_healthy": True, "total_keys": 5})
    return client


@pytest.fixture
def mock_wireguard_client():
    """Mock WireGuardClient."""
    client = AsyncMock()
    client.create_peer = AsyncMock(return_value={
        "client_name": "wg-client-123",
        "config": "[Interface]\nPrivateKey = xxx\nAddress = 10.0.0.2/24\n",
    })
    client.delete_client = AsyncMock(return_value=True)
    client.get_peer_metrics = AsyncMock(return_value={"transfer_total": 2048})
    client.get_usage = AsyncMock(return_value=[{"total": 1024}])
    return client


@pytest.fixture
def sample_user():
    """Sample User entity for tests."""
    return User(
        telegram_id=123456789,
        username="testuser",
        full_name="Test User",
        status=UserStatus.ACTIVE,
        max_keys=2,
        balance_stars=100,
        total_deposited=50,
    )


@pytest.fixture
def sample_vpn_key():
    """Sample VpnKey entity for tests."""
    return VpnKey(
        id=uuid.uuid4(),
        user_id=123456789,
        key_type=KeyType.OUTLINE,
        name="Test Key",
        key_data="ss://test@server:1234#TestKey",
        external_id="outline-key-123",
        is_active=True,
        used_bytes=0,
        data_limit_bytes=10 * 1024**3,
    )


@pytest.fixture
def sample_data_package():
    """Sample DataPackage entity for tests."""
    return DataPackage(
        id=uuid.uuid4(),
        user_id=123456789,
        package_type=PackageType.BASIC,
        data_limit_bytes=10 * 1024**3,
        stars_paid=50,
        expires_at=datetime.now(timezone.utc) + timedelta(days=35),
    )
```

**Step 2: Run tests to verify fixtures work**

Run: `pytest tests/ -v --collect-only`
Expected: All tests collected, no errors

**Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add shared fixtures for unit testing"
```

---

## Task 2: Create VpnService Tests

**Files:**
- Create: `tests/application/services/test_vpn_service.py`

**Step 1: Write failing tests for VpnService**

```python
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from application.services.vpn_service import VpnService
from domain.entities.user import User, UserRole
from domain.entities.vpn_key import VpnKey, KeyType


@pytest.fixture
def vpn_service(mock_user_repo, mock_key_repo, mock_outline_client, mock_wireguard_client):
    return VpnService(
        user_repo=mock_user_repo,
        key_repo=mock_key_repo,
        outline_client=mock_outline_client,
        wireguard_client=mock_wireguard_client,
    )


class TestCreateKey:
    @pytest.mark.asyncio
    async def test_create_outline_key_success(self, vpn_service, mock_user_repo, mock_key_repo, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_key_repo.save.return_value = VpnKey(
            id=uuid.uuid4(),
            user_id=123456789,
            key_type=KeyType.OUTLINE,
            name="Mi iPhone",
            key_data="ss://test@server:1234#TestKey",
            external_id="outline-key-123",
        )

        key = await vpn_service.create_key(
            telegram_id=123456789,
            key_type="outline",
            key_name="Mi iPhone",
            current_user_id=123456789,
        )

        assert key is not None
        assert key.key_type == KeyType.OUTLINE
        assert key.name == "Mi iPhone"
        mock_key_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_wireguard_key_success(self, vpn_service, mock_user_repo, mock_key_repo, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_key_repo.save.return_value = VpnKey(
            id=uuid.uuid4(),
            user_id=123456789,
            key_type=KeyType.WIREGUARD,
            name="Mi Laptop",
            key_data="[Interface]\nPrivateKey = xxx",
            external_id="wg-client-123",
        )

        key = await vpn_service.create_key(
            telegram_id=123456789,
            key_type="wireguard",
            key_name="Mi Laptop",
            current_user_id=123456789,
        )

        assert key is not None
        assert key.key_type == KeyType.WIREGUARD
        mock_key_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_key_auto_creates_user(self, vpn_service, mock_user_repo, mock_key_repo):
        mock_user_repo.get_by_id.return_value = None
        mock_user_repo.save.return_value = User(telegram_id=123456789)
        mock_key_repo.save.return_value = VpnKey(
            id=uuid.uuid4(),
            user_id=123456789,
            key_type=KeyType.OUTLINE,
            name="Test Key",
            key_data="ss://test",
            external_id="key-123",
        )

        await vpn_service.create_key(
            telegram_id=123456789,
            key_type="outline",
            key_name="Test Key",
            current_user_id=123456789,
        )

        mock_user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_key_raises_when_limit_reached(self, vpn_service, mock_user_repo, sample_user):
        sample_user._keys = [MagicMock(is_active=True), MagicMock(is_active=True)]
        mock_user_repo.get_by_id.return_value = sample_user

        with pytest.raises(ValueError, match="límite"):
            await vpn_service.create_key(
                telegram_id=123456789,
                key_type="outline",
                key_name="Test",
                current_user_id=123456789,
            )

    @pytest.mark.asyncio
    async def test_create_key_invalid_type_raises(self, vpn_service, mock_user_repo, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user

        with pytest.raises(ValueError, match="no soportado"):
            await vpn_service.create_key(
                telegram_id=123456789,
                key_type="invalid",
                key_name="Test",
                current_user_id=123456789,
            )


class TestRevokeKey:
    @pytest.mark.asyncio
    async def test_revoke_key_success(self, vpn_service, mock_key_repo, mock_user_repo, sample_vpn_key, sample_user):
        mock_key_repo.get_by_id.return_value = sample_vpn_key
        mock_user_repo.get_by_id.return_value = sample_user
        sample_user.total_deposited = 100
        mock_key_repo.delete.return_value = True

        result = await vpn_service.revoke_key(sample_vpn_key.id, 123456789)

        assert result is True
        mock_key_repo.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_key_not_found(self, vpn_service, mock_key_repo):
        mock_key_repo.get_by_id.return_value = None

        result = await vpn_service.revoke_key(uuid.uuid4(), 123456789)

        assert result is False

    @pytest.mark.asyncio
    async def test_revoke_key_user_cannot_delete(self, vpn_service, mock_key_repo, mock_user_repo, sample_vpn_key, sample_user):
        sample_user.total_deposited = 0
        mock_key_repo.get_by_id.return_value = sample_vpn_key
        mock_user_repo.get_by_id.return_value = sample_user

        with pytest.raises(ValueError, match="depósito"):
            await vpn_service.revoke_key(sample_vpn_key.id, 123456789)


class TestGetUserStatus:
    @pytest.mark.asyncio
    async def test_get_user_status_returns_summary(self, vpn_service, mock_user_repo, mock_key_repo, sample_user, sample_vpn_key):
        mock_user_repo.get_by_id.return_value = sample_user
        sample_vpn_key.used_bytes = 5 * 1024**3
        mock_key_repo.get_by_user_id.return_value = [sample_vpn_key]

        status = await vpn_service.get_user_status(123456789, 123456789)

        assert status["user"] == sample_user
        assert status["keys_count"] == 1
        assert status["total_used_gb"] == pytest.approx(5.0)
        mock_user_repo.get_by_id.assert_called_once()
        mock_key_repo.get_by_user_id.assert_called_once()


class TestFetchRealUsage:
    @pytest.mark.asyncio
    async def test_fetch_outline_usage(self, vpn_service, mock_outline_client, sample_vpn_key):
        sample_vpn_key.key_type = KeyType.OUTLINE
        sample_vpn_key.external_id = "outline-key-123"
        mock_outline_client.get_metrics.return_value = {"outline-key-123": 2048}

        usage = await vpn_service.fetch_real_usage(sample_vpn_key)

        assert usage == 2048

    @pytest.mark.asyncio
    async def test_fetch_wireguard_usage(self, vpn_service, mock_wireguard_client, sample_vpn_key):
        sample_vpn_key.key_type = KeyType.WIREGUARD
        sample_vpn_key.external_id = "wg-client-123"
        mock_wireguard_client.get_peer_metrics.return_value = {"transfer_total": 4096}

        usage = await vpn_service.fetch_real_usage(sample_vpn_key)

        assert usage == 4096

    @pytest.mark.asyncio
    async def test_fetch_usage_returns_zero_on_error(self, vpn_service, mock_outline_client, sample_vpn_key):
        sample_vpn_key.key_type = KeyType.OUTLINE
        mock_outline_client.get_metrics.side_effect = Exception("Connection error")

        usage = await vpn_service.fetch_real_usage(sample_vpn_key)

        assert usage == 0


class TestRenameKey:
    @pytest.mark.asyncio
    async def test_rename_key_success(self, vpn_service, mock_key_repo, sample_vpn_key):
        mock_key_repo.get_by_id.return_value = sample_vpn_key
        mock_key_repo.save.return_value = sample_vpn_key

        result = await vpn_service.rename_key(str(sample_vpn_key.id), "New Name", 123456789)

        assert result is True
        mock_key_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_rename_key_not_found(self, vpn_service, mock_key_repo):
        mock_key_repo.get_by_id.return_value = None

        result = await vpn_service.rename_key(str(uuid.uuid4()), "New Name", 123456789)

        assert result is False


class TestCanUserCreateKey:
    @pytest.mark.asyncio
    async def test_can_create_returns_true(self, vpn_service, mock_key_repo, sample_user):
        mock_key_repo.get_by_user_id.return_value = [MagicMock()]

        can_create, message = await vpn_service.can_user_create_key(sample_user, 123456789)

        assert can_create is True
        assert message == ""

    @pytest.mark.asyncio
    async def test_cannot_create_when_limit_reached(self, vpn_service, mock_key_repo, sample_user):
        mock_key_repo.get_by_user_id.return_value = [MagicMock(), MagicMock()]

        can_create, message = await vpn_service.can_user_create_key(sample_user, 123456789)

        assert can_create is False
        assert "límite" in message.lower()


class TestGetServerStatus:
    @pytest.mark.asyncio
    async def test_get_outline_server_status(self, vpn_service, mock_outline_client):
        mock_outline_client.get_server_info.return_value = {"is_healthy": True, "total_keys": 10}

        status = await vpn_service.get_server_status("outline")

        assert status["location"] == "Miami, USA"
        assert status["ping"] == 35

    @pytest.mark.asyncio
    async def test_get_wireguard_server_status(self, vpn_service, mock_wireguard_client):
        mock_wireguard_client.get_usage.return_value = [{"total": 1024}, {"total": 2048}]

        status = await vpn_service.get_server_status("wireguard")

        assert status["location"] == "Miami, USA"

    @pytest.mark.asyncio
    async def test_get_server_status_handles_error(self, vpn_service, mock_outline_client):
        mock_outline_client.get_server_info.side_effect = Exception("Error")

        status = await vpn_service.get_server_status("outline")

        assert status["location"] == "Miami, USA"
```

**Step 2: Run tests to verify they pass**

Run: `pytest tests/application/services/test_vpn_service.py -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/application/services/test_vpn_service.py
git commit -m "test: add VpnService unit tests"
```

---

## Task 3: Create PaymentService Tests

**Files:**
- Create: `tests/application/services/test_payment_service.py`

**Step 1: Write failing tests for PaymentService**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from application.services.payment_service import PaymentService
from domain.entities.user import User, UserRole


@pytest.fixture
def payment_service(mock_user_repo, mock_transaction_repo):
    return PaymentService(
        user_repo=mock_user_repo,
        transaction_repo=mock_transaction_repo,
    )


class TestUpdateBalance:
    @pytest.mark.asyncio
    async def test_update_balance_deposit_increases(self, payment_service, mock_user_repo, sample_user):
        sample_user.balance_stars = 100
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.save.return_value = sample_user

        result = await payment_service.update_balance(
            telegram_id=123456789,
            amount=50,
            transaction_type="deposit",
            description="Test deposit",
            current_user_id=123456789,
        )

        assert result is True
        assert sample_user.balance_stars == 150

    @pytest.mark.asyncio
    async def test_update_balance_records_transaction(self, payment_service, mock_user_repo, mock_transaction_repo, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.save.return_value = sample_user

        await payment_service.update_balance(
            telegram_id=123456789,
            amount=50,
            transaction_type="deposit",
            description="Test deposit",
            current_user_id=123456789,
        )

        mock_transaction_repo.record_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_balance_user_not_found(self, payment_service, mock_user_repo):
        mock_user_repo.get_by_id.return_value = None

        result = await payment_service.update_balance(
            telegram_id=999,
            amount=50,
            transaction_type="deposit",
            description="Test",
            current_user_id=999,
        )

        assert result is False


class TestDeductBalance:
    @pytest.mark.asyncio
    async def test_deduct_balance_success(self, payment_service, mock_user_repo, sample_user):
        sample_user.balance_stars = 100
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.save.return_value = sample_user

        result = await payment_service.deduct_balance(
            telegram_id=123456789,
            amount=30,
            description="Purchase",
            current_user_id=123456789,
        )

        assert result is True
        assert sample_user.balance_stars == 70

    @pytest.mark.asyncio
    async def test_deduct_balance_insufficient(self, payment_service, mock_user_repo, sample_user):
        sample_user.balance_stars = 10
        mock_user_repo.get_by_id.return_value = sample_user

        result = await payment_service.deduct_balance(
            telegram_id=123456789,
            amount=50,
            description="Purchase",
            current_user_id=123456789,
        )

        assert result is False


class TestGetUserBalance:
    @pytest.mark.asyncio
    async def test_get_user_balance_returns_value(self, payment_service, mock_user_repo, sample_user):
        sample_user.balance_stars = 150
        mock_user_repo.get_by_id.return_value = sample_user

        balance = await payment_service.get_user_balance(123456789, current_user_id=123456789)

        assert balance == 150

    @pytest.mark.asyncio
    async def test_get_user_balance_not_found(self, payment_service, mock_user_repo):
        mock_user_repo.get_by_id.return_value = None

        balance = await payment_service.get_user_balance(999, current_user_id=999)

        assert balance is None


class TestActivateVip:
    @pytest.mark.asyncio
    async def test_activate_vip_sets_expiry(self, payment_service, mock_user_repo, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.save.return_value = sample_user

        result = await payment_service.activate_vip(123456789, days=30, current_user_id=123456789)

        assert result is True
        assert sample_user.is_vip is True
        assert sample_user.vip_expires_at is not None


class TestAddStorage:
    @pytest.mark.asyncio
    async def test_add_storage_increases(self, payment_service, mock_user_repo, sample_user):
        sample_user.storage_gb = 10
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.save.return_value = sample_user

        result = await payment_service.add_storage(123456789, gb=5, current_user_id=123456789)

        assert result is True
        assert sample_user.storage_gb == 15
```

**Step 2: Run tests**

Run: `pytest tests/application/services/test_payment_service.py -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/application/services/test_payment_service.py
git commit -m "test: add PaymentService unit tests"
```

---

## Task 4: Create UserRepository Tests

**Files:**
- Create: `tests/infrastructure/persistence/test_user_repository.py`

**Step 1: Write failing tests for PostgresUserRepository**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from domain.entities.user import User, UserStatus
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository


@pytest.fixture
def repository(mock_session):
    return PostgresUserRepository(mock_session)


@pytest.fixture
def sample_user_model():
    model = MagicMock()
    model.telegram_id = 123456789
    model.username = "testuser"
    model.full_name = "Test User"
    model.status = "active"
    model.max_keys = 2
    model.balance_stars = 100
    model.total_deposited = 50
    model.referral_code = "ABC123"
    model.referred_by = None
    model.total_referral_earnings = 0
    model.is_vip = False
    model.vip_expires_at = None
    model.free_data_limit_bytes = 0
    model.free_data_used_bytes = 0
    return model


class TestGetById:
    @pytest.mark.asyncio
    async def test_get_by_id_returns_user(self, repository, mock_session, sample_user_model):
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_user_model

        result = await repository.get_by_id(123456789, current_user_id=123456789)

        assert result is not None
        assert result.telegram_id == 123456789
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none(self, repository, mock_session):
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        result = await repository.get_by_id(999, current_user_id=123456789)

        assert result is None


class TestSave:
    @pytest.mark.asyncio
    async def test_save_new_user(self, repository, mock_session):
        mock_session.get.return_value = None
        user = User(telegram_id=123456789, username="newuser")

        result = await repository.save(user, current_user_id=123456789)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result.telegram_id == 123456789

    @pytest.mark.asyncio
    async def test_save_existing_user(self, repository, mock_session, sample_user_model):
        mock_session.get.return_value = sample_user_model
        user = User(telegram_id=123456789, username="updateduser", full_name="Updated")

        await repository.save(user, current_user_id=123456789)

        mock_session.commit.assert_called_once()


class TestExists:
    @pytest.mark.asyncio
    async def test_exists_returns_true(self, repository, mock_session):
        mock_session.execute.return_value.scalar_one_or_none.return_value = 123456789

        result = await repository.exists(123456789, current_user_id=123456789)

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false(self, repository, mock_session):
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        result = await repository.exists(999, current_user_id=123456789)

        assert result is False


class TestGetByReferralCode:
    @pytest.mark.asyncio
    async def test_get_by_referral_code_found(self, repository, mock_session, sample_user_model):
        sample_user_model.referral_code = "ABC123"
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_user_model

        result = await repository.get_by_referral_code("ABC123", current_user_id=123456789)

        assert result is not None
        assert result.referral_code == "ABC123"

    @pytest.mark.asyncio
    async def test_get_by_referral_code_not_found(self, repository, mock_session):
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        result = await repository.get_by_referral_code("INVALID", current_user_id=123456789)

        assert result is None


class TestUpdateBalance:
    @pytest.mark.asyncio
    async def test_update_balance_success(self, repository, mock_session):
        mock_session.execute.return_value = None

        result = await repository.update_balance(123456789, 200, current_user_id=123456789)

        mock_session.commit.assert_called_once()
        assert result is True


class TestGetReferrals:
    @pytest.mark.asyncio
    async def test_get_referrals_returns_list(self, repository, mock_session, sample_user_model):
        mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_user_model]

        result = await repository.get_referrals(123456789, current_user_id=123456789)

        assert isinstance(result, list)
```

**Step 2: Run tests**

Run: `pytest tests/infrastructure/persistence/test_user_repository.py -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/infrastructure/persistence/test_user_repository.py
git commit -m "test: add UserRepository unit tests"
```

---

## Task 5: Create KeyRepository Tests

**Files:**
- Create: `tests/infrastructure/persistence/test_key_repository.py`

**Step 1: Write failing tests for PostgresKeyRepository**

```python
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.entities.vpn_key import VpnKey, KeyType
from infrastructure.persistence.postgresql.key_repository import PostgresKeyRepository


@pytest.fixture
def repository(mock_session):
    return PostgresKeyRepository(mock_session)


@pytest.fixture
def sample_key_model():
    model = MagicMock()
    model.id = uuid.uuid4()
    model.user_id = 123456789
    model.key_type = "outline"
    model.name = "Test Key"
    model.key_data = "ss://test@server:1234#TestKey"
    model.external_id = "outline-key-123"
    model.created_at = datetime.now(timezone.utc)
    model.is_active = True
    model.used_bytes = 0
    model.last_seen_at = None
    model.data_limit_bytes = 10 * 1024**3
    model.billing_reset_at = datetime.now(timezone.utc)
    return model


class TestSave:
    @pytest.mark.asyncio
    async def test_save_new_key(self, repository, mock_session):
        mock_session.get.return_value = None
        key = VpnKey(
            id=uuid.uuid4(),
            user_id=123456789,
            key_type=KeyType.OUTLINE,
            name="New Key",
            key_data="ss://test",
            external_id="key-123",
        )

        result = await repository.save(key, current_user_id=123456789)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_existing_key(self, repository, mock_session, sample_key_model):
        mock_session.get.return_value = sample_key_model
        key = VpnKey(
            id=sample_key_model.id,
            user_id=123456789,
            key_type=KeyType.OUTLINE,
            name="Updated Key",
            key_data="ss://updated",
            external_id="key-123",
        )

        await repository.save(key, current_user_id=123456789)

        mock_session.commit.assert_called_once()


class TestGetByUserId:
    @pytest.mark.asyncio
    async def test_get_by_user_id_returns_keys(self, repository, mock_session, sample_key_model):
        mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_key_model]

        result = await repository.get_by_user_id(123456789, current_user_id=123456789)

        assert len(result) == 1
        assert result[0].user_id == 123456789

    @pytest.mark.asyncio
    async def test_get_by_user_id_returns_empty(self, repository, mock_session):
        mock_session.execute.return_value.scalars.return_value.all.return_value = []

        result = await repository.get_by_user_id(999, current_user_id=123456789)

        assert result == []


class TestGetAllActive:
    @pytest.mark.asyncio
    async def test_get_all_active_returns_only_active(self, repository, mock_session, sample_key_model):
        mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_key_model]

        result = await repository.get_all_active(current_user_id=123456789)

        assert len(result) == 1
        assert result[0].is_active is True


class TestGetById:
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repository, mock_session, sample_key_model):
        mock_session.get.return_value = sample_key_model

        result = await repository.get_by_id(sample_key_model.id, current_user_id=123456789)

        assert result is not None
        assert result.id == sample_key_model.id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_session):
        mock_session.get.return_value = None

        result = await repository.get_by_id(uuid.uuid4(), current_user_id=123456789)

        assert result is None


class TestDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, repository, mock_session):
        mock_session.execute.return_value = None

        result = await repository.delete(uuid.uuid4(), current_user_id=123456789)

        mock_session.commit.assert_called_once()
        assert result is True


class TestUpdateUsage:
    @pytest.mark.asyncio
    async def test_update_usage_success(self, repository, mock_session):
        mock_session.execute.return_value = None

        result = await repository.update_usage(uuid.uuid4(), 1024, current_user_id=123456789)

        mock_session.commit.assert_called_once()
        assert result is True


class TestResetDataUsage:
    @pytest.mark.asyncio
    async def test_reset_data_usage_success(self, repository, mock_session):
        mock_session.execute.return_value = None

        result = await repository.reset_data_usage(uuid.uuid4(), current_user_id=123456789)

        mock_session.commit.assert_called_once()
        assert result is True
```

**Step 2: Run tests**

Run: `pytest tests/infrastructure/persistence/test_key_repository.py -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/infrastructure/persistence/test_key_repository.py
git commit -m "test: add KeyRepository unit tests"
```

---

## Task 6: Run Full Test Suite

**Step 1: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests pass

**Step 2: Verify test count**

Run: `pytest --collect-only | tail -5`
Expected: ~88 tests collected

**Step 3: Commit**

```bash
git add docs/plans/
git commit -m "docs: add testing system design and implementation plan"
```

---

## Summary

After completing all tasks:
- [x] Shared fixtures in conftest.py
- [x] VpnService tests (~15 tests)
- [x] PaymentService tests (~10 tests)
- [x] UserRepository tests (~10 tests)
- [x] KeyRepository tests (~10 tests)
- [x] Full test suite passing
- [x] ~88 total tests
