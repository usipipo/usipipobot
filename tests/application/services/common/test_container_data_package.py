import pytest
from unittest.mock import AsyncMock


class TestDataPackageServiceDI:
    def test_container_has_data_package_service(self):
        from application.services.data_package_service import DataPackageService
        
        assert DataPackageService is not None
            
    def test_data_package_service_requires_repos(self):
        from application.services.data_package_service import DataPackageService
        
        mock_package_repo = AsyncMock()
        mock_user_repo = AsyncMock()
        
        service = DataPackageService(
            package_repo=mock_package_repo,
            user_repo=mock_user_repo
        )
        
        assert service.package_repo is mock_package_repo
        assert service.user_repo is mock_user_repo

    def test_container_registration_exists(self):
        from application.services.common.container import _configure_application_services
        import punq
        
        container = punq.Container()
        _configure_application_services(container)
        
        from application.services.data_package_service import DataPackageService
        
        service = container.resolve(DataPackageService)
        assert service is not None
        assert isinstance(service, DataPackageService)
