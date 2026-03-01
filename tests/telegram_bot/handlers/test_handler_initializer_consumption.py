"""
Test para verificar el registro de handlers de consumo.

Verifica que los handlers del módulo de tarifa por consumo
estén correctamente registrados en el inicializador.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestConsumptionHandlersRegistration:
    """Tests para verificar registro de handlers de consumo."""

    @pytest.fixture
    def mock_container(self):
        """Mock del contenedor DI."""
        container = MagicMock()
        
        # Mock de servicios necesarios
        mock_billing_service = MagicMock()
        mock_invoice_service = MagicMock()
        mock_admin_service = MagicMock()
        mock_ticket_service = MagicMock()
        mock_vpn_infra_service = MagicMock()
        mock_referral_service = MagicMock()
        mock_data_package_service = MagicMock()
        mock_user_profile_service = MagicMock()
        mock_crypto_order_repo = MagicMock()
        
        def resolve_side_effect(service_class):
            services = {
                'AdminService': mock_admin_service,
                'TicketService': mock_ticket_service,
                'VpnInfrastructureService': mock_vpn_infra_service,
                'ReferralService': mock_referral_service,
                'DataPackageService': mock_data_package_service,
                'UserProfileService': mock_user_profile_service,
                'ConsumptionBillingService': mock_billing_service,
                'ConsumptionInvoiceService': mock_invoice_service,
            }
            service_name = service_class.__name__ if hasattr(service_class, '__name__') else str(service_class)
            for key, value in services.items():
                if key in service_name:
                    return value
            return MagicMock()
        
        container.resolve.side_effect = resolve_side_effect
        return container

    @pytest.fixture
    def mock_vpn_service(self):
        """Mock del VpnService."""
        return MagicMock()

    @pytest.fixture
    def mock_referral_service(self):
        """Mock del ReferralService."""
        return MagicMock()

    @patch('telegram_bot.handlers.handler_initializer.get_container')
    def test_consumption_handlers_are_registered(
        self, mock_get_container, mock_container, mock_vpn_service, mock_referral_service
    ):
        """
        Verifica que los handlers de consumo están registrados.
        
        Este test valida que:
        1. Los handlers de consumo se incluyen en la lista de handlers
        2. Se resuelven los servicios necesarios del contenedor
        3. Se registran tanto handlers como callback handlers
        """
        mock_get_container.return_value = mock_container
        
        from telegram_bot.handlers.handler_initializer import initialize_handlers
        
        handlers = initialize_handlers(mock_vpn_service, mock_referral_service)
        
        # Verificar que se resolvieron los servicios de consumo
        mock_container.resolve.assert_any_call(
            __import__('application.services.consumption_billing_service', fromlist=['ConsumptionBillingService']).ConsumptionBillingService
        )
        mock_container.resolve.assert_any_call(
            __import__('application.services.consumption_invoice_service', fromlist=['ConsumptionInvoiceService']).ConsumptionInvoiceService
        )
        
        # Verificar que se agregaron handlers (debería haber más de 0)
        assert len(handlers) > 0

    @patch('telegram_bot.handlers.handler_initializer.get_container')
    def test_get_consumption_handlers_returns_list(
        self, mock_get_container, mock_container
    ):
        """
        Verifica que _get_consumption_handlers retorna una lista.
        """
        mock_get_container.return_value = mock_container
        
        from telegram_bot.handlers.handler_initializer import _get_consumption_handlers
        
        handlers = _get_consumption_handlers(mock_container)
        
        assert isinstance(handlers, list)
        assert len(handlers) >= 2  # CommandHandler + CallbackQueryHandlers

    def test_consumption_handler_functions_exist(self):
        """
        Verifica que las funciones de handlers de consumo existen y son importables.
        """
        from telegram_bot.features.consumption import (
            get_consumption_handlers,
            get_consumption_callback_handlers,
            ConsumptionHandler,
        )
        
        assert callable(get_consumption_handlers)
        assert callable(get_consumption_callback_handlers)
        assert callable(ConsumptionHandler)

    def test_consumption_callbacks_defined(self):
        """
        Verifica que los callbacks esperados están definidos.
        """
        from telegram_bot.features.consumption.handlers_consumption import (
            get_consumption_callback_handlers,
        )
        
        mock_billing = MagicMock()
        mock_invoice = MagicMock()
        
        handlers = get_consumption_callback_handlers(mock_billing, mock_invoice)
        
        # Verificar que hay handlers para los callbacks principales
        callback_patterns = []
        for handler in handlers:
            if hasattr(handler, 'pattern'):
                pattern = handler.pattern
                if hasattr(pattern, 'pattern'):
                    callback_patterns.append(pattern.pattern)
                else:
                    callback_patterns.append(str(pattern))
        
        # Verificar que los callbacks clave están presentes
        expected_patterns = [
            'consumption_menu',
            'consumption_activate',
            'consumption_confirm_activate',
            'consumption_view_status',
            'consumption_generate_invoice',
        ]
        
        for expected in expected_patterns:
            found = any(expected in pattern for pattern in callback_patterns)
            assert found, f"Callback '{expected}' no encontrado en handlers"
