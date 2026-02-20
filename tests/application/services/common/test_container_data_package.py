# tests/application/services/common/test_container_data_package.py
import pytest
from application.services.common.container import get_container, get_service
from application.services.data_package_service import DataPackageService

class TestDataPackageServiceDI:
    def test_container_has_data_package_service(self):
        container = get_container()
        service = container.resolve(DataPackageService)
        
        assert service is not None
        assert isinstance(service, DataPackageService)
    
    def test_get_service_returns_data_package_service(self):
        service = get_service(DataPackageService)
        
        assert isinstance(service, DataPackageService)
