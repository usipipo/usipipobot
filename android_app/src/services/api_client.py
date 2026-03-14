"""
HTTP client for API communication with JWT handling.
"""
import httpx
from loguru import logger
from typing import Optional, Dict, Any

from src.config import BASE_URL, REQUEST_TIMEOUT
from src.storage.secure_storage import SecureStorage


class ApiClient:
    """Async HTTP client with automatic JWT injection."""

    def __init__(self, telegram_id: Optional[str] = None):
        self.base_url = BASE_URL
        self.telegram_id = telegram_id
        self.timeout = REQUEST_TIMEOUT

    async def _get_headers(self) -> Dict[str, str]:
        """Get headers with JWT token if available."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.telegram_id:
            token = SecureStorage.get_jwt(self.telegram_id)
            if token:
                headers["Authorization"] = f"Bearer {token}"

        return headers

    async def post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        use_auth: bool = False
    ) -> Dict[str, Any]:
        """Make POST request."""
        url = f"{self.base_url}{endpoint}"
        headers = await self._get_headers() if use_auth else {}

        logger.debug(f"POST {url}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                raise

    async def get(
        self,
        endpoint: str,
        use_auth: bool = False
    ) -> Dict[str, Any]:
        """Make GET request."""
        url = f"{self.base_url}{endpoint}"
        headers = await self._get_headers() if use_auth else {}

        logger.debug(f"GET {url}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                raise
