from unittest.mock import AsyncMock, MagicMock

import pytest

from config import settings
from infrastructure.jobs.package_expiration_job import expire_packages_job


class TestExpirePackagesJob:
    @pytest.mark.asyncio
    async def test_job_calls_expire_old_packages(self):
        mock_service = AsyncMock()
        mock_service.expire_old_packages.return_value = 5

        context = MagicMock()
        context.job.data = {"data_package_service": mock_service}

        await expire_packages_job(context)

        mock_service.expire_old_packages.assert_called_once_with(
            admin_user_id=settings.ADMIN_ID
        )

    @pytest.mark.asyncio
    async def test_job_handles_exception(self):
        mock_service = AsyncMock()
        mock_service.expire_old_packages.side_effect = Exception("DB error")

        context = MagicMock()
        context.job.data = {"data_package_service": mock_service}

        await expire_packages_job(context)
