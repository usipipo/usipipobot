"""
Tests de integración para endpoints /api/v1/auth

Requiere: Redis corriendo, DB de test configurada
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from config import settings
from infrastructure.api.android.auth import router
from infrastructure.api.android.deps import get_current_user


def create_test_app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return app


async def fake_get_current_user():
    """Fake get_current_user dependency."""
    return {
        "sub": "123456789",
        "client": "android_apk",
        "jti": "test-jti-123",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp()),
    }


async def fake_get_current_user_revoked():
    """Fake get_current_user that raises token_revoked."""
    from fastapi import HTTPException

    raise HTTPException(
        status_code=401,
        detail={"error": "token_revoked", "message": "Sesión cerrada. Inicia sesión nuevamente."},
    )


@pytest.fixture
def mock_redis():
    """Fixture: Mock Redis connection."""
    with patch("infrastructure.api.android.auth.redis") as mock:
        redis_instance = MagicMock()
        redis_instance.__aenter__ = AsyncMock(return_value=redis_instance)
        redis_instance.__aexit__ = AsyncMock(return_value=None)
        redis_instance.incr = AsyncMock(return_value=1)
        redis_instance.expire = AsyncMock(return_value=True)
        redis_instance.ttl = AsyncMock(return_value=3600)
        redis_instance.setex = AsyncMock(return_value=True)
        redis_instance.get = AsyncMock(return_value=None)
        redis_instance.delete = AsyncMock(return_value=1)
        redis_instance.exists = AsyncMock(return_value=0)
        mock.from_url.return_value = redis_instance
        yield mock


@pytest.fixture
def mock_db_session():
    """Fixture: Mock database session."""
    with patch("infrastructure.api.android.auth.get_session_context") as mock:
        session = AsyncMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=None)
        session.execute = AsyncMock()
        mock.return_value = session
        yield session


class TestRequestOTP:
    """Tests for POST /auth/request-otp endpoint."""

    @pytest.mark.asyncio
    async def test_request_otp_user_not_found(self, mock_redis, mock_db_session):
        """Test request_otp when user doesn't exist → 404."""
        # Arrange: Mock DB returns None
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        test_app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            # Act
            response = await ac.post(
                "/api/v1/auth/request-otp", json={"identifier": "@nonexistent"}
            )

            # Assert
            assert response.status_code == 404
            assert response.json()["detail"]["error"] == "user_not_found"

    @pytest.mark.asyncio
    async def test_request_otp_user_inactive(self, mock_redis, mock_db_session):
        """Test request_otp when user is inactive → 403."""
        # Arrange: Mock DB returns inactive user
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            telegram_id=123, username="testuser", status="suspended"
        )
        mock_db_session.execute.return_value = mock_result

        test_app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            # Act
            response = await ac.post("/api/v1/auth/request-otp", json={"identifier": "@testuser"})

            # Assert
            assert response.status_code == 403
            assert response.json()["detail"]["error"] == "user_inactive"

    @pytest.mark.asyncio
    async def test_request_otp_rate_limit_ip(self, mock_redis, mock_db_session):
        """Test request_otp rate limit by IP → 429."""
        # Arrange: Mock Redis returns > 5 requests from IP
        mock_redis.from_url.return_value.__aenter__.return_value.incr = AsyncMock(return_value=6)

        test_app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            # Act
            response = await ac.post("/api/v1/auth/request-otp", json={"identifier": "@testuser"})

            # Assert
            assert response.status_code == 429
            assert response.json()["detail"]["error"] == "rate_limit_exceeded"

    @pytest.mark.asyncio
    async def test_request_otp_rate_limit_identifier(self, mock_redis, mock_db_session):
        """Test request_otp rate limit by identifier → 429."""
        # Arrange: Mock Redis returns 1 for IP, > 3 for identifier
        redis_instance = mock_redis.from_url.return_value.__aenter__.return_value
        redis_instance.incr = AsyncMock(side_effect=[1, 4])  # IP=1, identifier=4

        test_app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            # Act
            response = await ac.post("/api/v1/auth/request-otp", json={"identifier": "@testuser"})

            # Assert
            assert response.status_code == 429
            assert response.json()["detail"]["error"] == "rate_limit_exceeded"


class TestVerifyOTP:
    """Tests for POST /auth/verify-otp endpoint."""

    @pytest.mark.asyncio
    async def test_verify_otp_invalid(self, mock_redis, mock_db_session):
        """Test verify_otp with wrong OTP → 401 + attempts_remaining."""
        # Arrange: Mock DB returns active user
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            telegram_id=123, username="testuser", full_name="Test User", status="active"
        )
        mock_db_session.execute.return_value = mock_result

        # Mock Redis returns stored OTP
        redis_instance = mock_redis.from_url.return_value.__aenter__.return_value
        redis_instance.get = AsyncMock(return_value=b"999999")  # Different OTP
        redis_instance.incr = AsyncMock(return_value=1)  # First fail
        redis_instance.expire = AsyncMock(return_value=True)

        test_app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            # Act
            response = await ac.post(
                "/api/v1/auth/verify-otp", json={"identifier": "@testuser", "otp": "123456"}
            )

            # Assert
            assert response.status_code == 401
            assert response.json()["detail"]["error"] == "invalid_otp"
            assert "attempts_remaining" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_verify_otp_expired(self, mock_redis, mock_db_session):
        """Test verify_otp with expired OTP → 401 otp_expired."""
        # Arrange: Mock DB returns active user
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            telegram_id=123, username="testuser", full_name="Test User", status="active"
        )
        mock_db_session.execute.return_value = mock_result

        # Mock Redis returns None (expired)
        redis_instance = mock_redis.from_url.return_value.__aenter__.return_value
        redis_instance.get = AsyncMock(return_value=None)

        test_app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            # Act
            response = await ac.post(
                "/api/v1/auth/verify-otp", json={"identifier": "@testuser", "otp": "123456"}
            )

            # Assert
            assert response.status_code == 401
            assert response.json()["detail"]["error"] == "otp_expired"

    @pytest.mark.asyncio
    async def test_verify_otp_too_many_attempts(self, mock_redis, mock_db_session):
        """Test verify_otp with too many failed attempts → 429."""
        # Arrange: Mock DB returns active user
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            telegram_id=123, username="testuser", full_name="Test User", status="active"
        )
        mock_db_session.execute.return_value = mock_result

        # Mock Redis returns wrong OTP and fail count = 3
        redis_instance = mock_redis.from_url.return_value.__aenter__.return_value
        redis_instance.get = AsyncMock(return_value=b"999999")
        redis_instance.incr = AsyncMock(return_value=3)  # Third fail

        test_app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            # Act
            response = await ac.post(
                "/api/v1/auth/verify-otp", json={"identifier": "@testuser", "otp": "123456"}
            )

            # Assert
            assert response.status_code == 429
            assert response.json()["detail"]["error"] == "too_many_attempts"

    @pytest.mark.asyncio
    async def test_verify_otp_success(self, mock_redis, mock_db_session):
        """Test verify_otp with correct OTP → 200 + access_token."""
        # Arrange: Mock DB returns active user
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            telegram_id=123, username="testuser", full_name="Test User", status="active"
        )
        mock_db_session.execute.return_value = mock_result

        # Mock Redis returns correct OTP
        redis_instance = mock_redis.from_url.return_value.__aenter__.return_value
        redis_instance.get = AsyncMock(return_value=b"123456")
        redis_instance.delete = AsyncMock(return_value=1)

        test_app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            # Act
            response = await ac.post(
                "/api/v1/auth/verify-otp", json={"identifier": "@testuser", "otp": "123456"}
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert data["expires_in"] == 86400
            assert data["user"]["telegram_id"] == 123
            assert data["user"]["username"] == "testuser"


class TestRefreshToken:
    """Tests for POST /auth/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_invalidates_old_token(self, mock_redis):
        """Test refresh invalidates old token (token rotation)."""
        # Arrange: Mock Redis for blacklist
        redis_instance = mock_redis.from_url.return_value.__aenter__.return_value
        redis_instance.setex = AsyncMock(return_value=True)

        test_app = create_test_app()
        test_app.dependency_overrides[get_current_user] = fake_get_current_user

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            # Act
            response = await ac.post("/api/v1/auth/refresh")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data

            # Verify old token was blacklisted
            redis_instance.setex.assert_called_once()
            call_args = redis_instance.setex.call_args
            assert "jwt:blacklist:test-jti-123" in call_args[0][0]


class TestLogout:
    """Tests for POST /auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_blacklists_token(self, mock_redis):
        """Test logout adds token to blacklist."""
        # Arrange: Mock Redis for blacklist
        redis_instance = mock_redis.from_url.return_value.__aenter__.return_value
        redis_instance.setex = AsyncMock(return_value=True)

        test_app = create_test_app()
        test_app.dependency_overrides[get_current_user] = fake_get_current_user

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            # Act
            response = await ac.post("/api/v1/auth/logout")

            # Assert
            assert response.status_code == 200
            assert response.json()["message"] == "Sesión cerrada"

            # Verify token was blacklisted
            redis_instance.setex.assert_called_once()


class TestMe:
    """Tests for GET /auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_me_with_valid_token(self, mock_db_session):
        """Test me endpoint with valid token → 200 + user data."""
        # Arrange: Mock DB returns user
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            telegram_id=123,
            username="testuser",
            full_name="Test User",
            status="active",
            has_pending_debt=False,
            consumption_mode_enabled=False,
        )
        mock_db_session.execute.return_value = mock_result

        test_app = create_test_app()
        test_app.dependency_overrides[get_current_user] = fake_get_current_user

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            # Act
            response = await ac.get("/api/v1/auth/me")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["telegram_id"] == 123
            assert data["username"] == "testuser"
            assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_me_with_revoked_token(self):
        """Test me endpoint with revoked token → 401."""
        test_app = create_test_app()
        test_app.dependency_overrides[get_current_user] = fake_get_current_user_revoked

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            # Act
            response = await ac.get("/api/v1/auth/me")

            # Assert
            assert response.status_code == 401
            assert response.json()["detail"]["error"] == "token_revoked"
