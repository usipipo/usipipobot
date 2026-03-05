"""
Test de regresión para verificar que created_at se preserva al cargar usuario.

Este test verifica el fix para el bug donde cada vez que se ejecutaba /start,
la fecha de registro se regeneraba con la fecha actual en lugar de preservar
la fecha original.

Author: uSipipo Team
Issue: created_at se regeneraba al cargar usuario existente
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from domain.entities.user import UserRole, UserStatus
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository


class TestUserCreatedAtPreservation:
    """Tests para verificar que created_at no se regenera al cargar usuario."""

    def test_model_to_entity_preserves_created_at(self):
        """
        Verifica que _model_to_entity preserve el created_at original.

        Bug original: El método _model_to_entity no incluía created_at,
        causando que se generara una nueva fecha cada vez que se cargaba
        un usuario existente.
        """
        # Arrange
        mock_session = MagicMock()
        repo = PostgresUserRepository(mock_session)

        # Crear mock de modelo con fecha específica en el pasado
        past_date = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        mock_model = MagicMock()
        mock_model.telegram_id = 123456
        mock_model.username = "testuser"
        mock_model.full_name = "Test User"
        mock_model.status = "active"
        mock_model.role = "user"
        mock_model.max_keys = 2
        mock_model.referral_code = "ABC123"
        mock_model.referred_by = None
        mock_model.referral_credits = 0
        mock_model.free_data_limit_bytes = 5 * 1024**3
        mock_model.free_data_used_bytes = 0
        mock_model.wallet_address = None
        mock_model.purchase_count = 0
        mock_model.loyalty_bonus_percent = 0
        mock_model.welcome_bonus_used = False
        mock_model.referred_users_with_purchase = 0
        mock_model.created_at = past_date  # Fecha en el pasado

        # Act
        entity = repo._model_to_entity(mock_model)

        # Assert
        assert entity.created_at == past_date, (
            f"created_at debería ser {past_date}, pero es {entity.created_at}. "
            "El bug causa que la fecha de registro se pierda al cargar usuario."
        )
        assert entity.telegram_id == 123456
        assert entity.username == "testuser"

    def test_model_to_entity_preserves_different_dates(self):
        """
        Verifica que funcione con diferentes fechas de registro.
        """
        mock_session = MagicMock()
        repo = PostgresUserRepository(mock_session)

        # Probar con múltiples fechas
        test_dates = [
            datetime(2023, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 12, 25, 0, 0, 0, tzinfo=timezone.utc),
            datetime(2022, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        ]

        for past_date in test_dates:
            mock_model = MagicMock()
            mock_model.telegram_id = 123456
            mock_model.username = "testuser"
            mock_model.full_name = "Test User"
            mock_model.status = "active"
            mock_model.role = "user"
            mock_model.max_keys = 2
            mock_model.referral_code = "ABC123"
            mock_model.referred_by = None
            mock_model.referral_credits = 0
            mock_model.free_data_limit_bytes = 5 * 1024**3
            mock_model.free_data_used_bytes = 0
            mock_model.wallet_address = None
            mock_model.purchase_count = 0
            mock_model.loyalty_bonus_percent = 0
            mock_model.welcome_bonus_used = False
            mock_model.referred_users_with_purchase = 0
            mock_model.created_at = past_date

            entity = repo._model_to_entity(mock_model)

            assert (
                entity.created_at == past_date
            ), f"Falla para fecha {past_date}: got {entity.created_at}"

    def test_model_to_entity_with_null_values(self):
        """
        Verifica que el modelo maneje correctamente valores nulos.
        """
        mock_session = MagicMock()
        repo = PostgresUserRepository(mock_session)

        past_date = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        mock_model = MagicMock()
        mock_model.telegram_id = 123456
        mock_model.username = None
        mock_model.full_name = None
        mock_model.status = None
        mock_model.role = None
        mock_model.max_keys = None
        mock_model.referral_code = None
        mock_model.referred_by = None
        mock_model.referral_credits = None
        mock_model.free_data_limit_bytes = None
        mock_model.free_data_used_bytes = None
        mock_model.wallet_address = None
        mock_model.purchase_count = None
        mock_model.loyalty_bonus_percent = None
        mock_model.welcome_bonus_used = None
        mock_model.referred_users_with_purchase = None
        mock_model.created_at = past_date

        entity = repo._model_to_entity(mock_model)

        assert entity.created_at == past_date
        assert entity.status == UserStatus.ACTIVE  # Default
        assert entity.role == UserRole.USER  # Default
        assert entity.max_keys == 2  # Default
