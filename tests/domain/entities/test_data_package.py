import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest

from domain.entities.data_package import DataPackage, PackageType


class TestPackageType:
    def test_package_type_has_all_required_values(self):
        assert PackageType.BASIC.value == "basic"
        assert PackageType.ESTANDAR.value == "estandar"
        assert PackageType.AVANZADO.value == "avanzado"
        assert PackageType.PREMIUM.value == "premium"
