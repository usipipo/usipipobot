"""
Keys service for VPN key management.
"""

from typing import Any, Dict, List, Optional

from loguru import logger
from src.services.api_client import ApiClient


class VpnKeyData:
    """Data class for VPN key information."""

    def __init__(self, data: dict):
        self.id = data.get("id", "")
        self.name = data.get("name", "Sin nombre")
        self.key_type = data.get("key_type", "outline")
        self.server = data.get("server", "")
        self.is_active = data.get("is_active", False)
        self.used_bytes = data.get("used_bytes", 0)
        self.data_limit_bytes = data.get("data_limit_bytes", 0)
        self.created_at = data.get("created_at", "")
        self.expires_at = data.get("expires_at")
        self.last_seen_at = data.get("last_seen_at")
        self.key_data = data.get("key_data", "")  # Connection string
        self.external_id = data.get("external_id")
        self.billing_reset_at = data.get("billing_reset_at")

    @property
    def server_display(self) -> str:
        """Get server display name based on key type."""
        if self.key_type == "outline":
            return "Outline"
        elif self.key_type == "wireguard":
            return "WireGuard"
        return self.server or "Unknown"

    @property
    def used_gb(self) -> float:
        """Get used data in GB."""
        return self.used_bytes / (1024**3)

    @property
    def limit_gb(self) -> float:
        """Get data limit in GB."""
        return self.data_limit_bytes / (1024**3)

    @property
    def remaining_gb(self) -> float:
        """Get remaining data in GB."""
        return max(0, self.data_limit_bytes - self.used_bytes) / (1024**3)

    @property
    def usage_percentage(self) -> float:
        """Get usage percentage."""
        if self.data_limit_bytes == 0:
            return 0.0
        return min(100.0, (self.used_bytes / self.data_limit_bytes) * 100)


class KeysService:
    """Service for managing VPN keys."""

    def __init__(self):
        self.api_client = ApiClient()

    async def list_keys(self) -> Dict[str, Any]:
        """
        List all VPN keys for the authenticated user.

        Returns:
            Dict with keys list and metadata:
            - keys: List of VpnKeyData
            - total_count: Total number of keys
            - active_count: Number of active keys
            - max_keys: Maximum allowed keys
        """
        logger.info("Listing VPN keys")

        response = await self.api_client.get("/keys", use_auth=True)

        # Parse keys
        keys_data = response.get("keys", [])
        keys = [VpnKeyData(k) for k in keys_data]

        return {
            "keys": keys,
            "total_count": response.get("total_count", 0),
            "active_count": response.get("active_count", 0),
            "max_keys": response.get("max_keys", 2),
        }

    async def get_key_detail(self, key_id: str) -> VpnKeyData:
        """
        Get detailed information for a specific VPN key.

        Args:
            key_id: UUID of the VPN key

        Returns:
            VpnKeyData with full key information including key_data
        """
        logger.info(f"Getting detail for VPN key {key_id}")

        response = await self.api_client.get(f"/keys/{key_id}", use_auth=True)
        return VpnKeyData(response)

    async def can_create_key(self) -> Dict[str, Any]:
        """
        Check if user can create new VPN keys.

        Returns:
            Dict with creation capability:
            - can_create: General ability to create keys
            - can_create_outline: Can create Outline keys
            - can_create_wireguard: Can create WireGuard keys
            - current_count: Current number of keys
            - max_keys: Maximum allowed keys
            - reason: Reason if cannot create (None otherwise)
        """
        logger.info("Checking key creation capability")

        response = await self.api_client.get("/keys/can-create", use_auth=True)
        return response

    async def create_key(self, key_type: str, name: str) -> Dict[str, Any]:
        """
        Create a new VPN key.

        Args:
            key_type: "outline" or "wireguard"
            name: Custom name for the key (max 30 chars)

        Returns:
            Dict with created key information:
            - id: Key ID
            - name: Key name
            - key_type: Type of key
            - key_data: Connection string
            - qr_data: Data for QR code
            - server: Server name
            - is_active: Whether key is active
            - data_limit_bytes: Data limit
            - created_at: Creation timestamp

        Raises:
            Exception: If key creation fails
        """
        logger.info(f"Creating {key_type} key with name '{name}'")

        response = await self.api_client.post(
            "/keys/create", data={"key_type": key_type, "name": name}, use_auth=True
        )

        logger.info(f"Key created successfully: {response.get('id')}")
        return response

    async def rename_key(self, key_id: str, new_name: str) -> Dict[str, Any]:
        """
        Rename a VPN key.

        Args:
            key_id: UUID of the VPN key
            new_name: New name (max 30 chars)

        Returns:
            Dict with success message and new name

        Raises:
            Exception: If rename fails
        """
        logger.info(f"Renaming key {key_id} to '{new_name}'")

        response = await self.api_client.patch(
            f"/keys/{key_id}", data={"name": new_name}, use_auth=True
        )

        logger.info(f"Key renamed successfully")
        return response

    async def delete_key(self, key_id: str) -> Dict[str, Any]:
        """
        Delete a VPN key.

        Args:
            key_id: UUID of the VPN key

        Returns:
            Dict with success message

        Raises:
            Exception: If deletion fails (e.g., insufficient credits)
        """
        logger.warning(f"Deleting key {key_id}")

        response = await self.api_client.delete(f"/keys/{key_id}", use_auth=True)

        logger.info(f"Key deleted successfully")
        return response

    async def get_key_usage(self, key_id: str) -> Dict[str, Any]:
        """
        Get detailed usage information for a VPN key.

        Args:
            key_id: UUID of the VPN key

        Returns:
            Dict with usage information:
            - used_bytes: Bytes used
            - data_limit_bytes: Total data limit
            - remaining_bytes: Bytes remaining
            - usage_percentage: Percentage used (0-100)
            - billing_reset_at: Next billing reset date
        """
        logger.info(f"Getting usage for key {key_id}")

        response = await self.api_client.get(f"/keys/{key_id}/usage", use_auth=True)
        return response

    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """
        Format bytes to human-readable string.

        Args:
            bytes_value: Bytes to format

        Returns:
            Formatted string (e.g., "1.5 GB", "250 MB")
        """
        if bytes_value >= 1_073_741_824:  # 1 GB
            return f"{bytes_value / 1_073_741_824:.2f} GB"
        elif bytes_value >= 1_048_576:  # 1 MB
            return f"{bytes_value / 1_048_576:.2f} MB"
        elif bytes_value >= 1_024:  # 1 KB
            return f"{bytes_value / 1_024:.2f} KB"
        else:
            return f"{bytes_value} B"
