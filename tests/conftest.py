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
        id=str(uuid.uuid4()),
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
