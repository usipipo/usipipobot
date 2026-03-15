"""
VPN Keys endpoints for Android APK.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import text

from domain.entities.vpn_key import KeyType
from infrastructure.api.android.deps import get_current_user
from infrastructure.api.android.keys_schemas import (
    CanCreateKeyResponse,
    CreateKeyRequest,
    CreateKeyResponse,
    KeysListResponse,
    KeyUsageInfo,
    RenameKeyRequest,
    VpnKeyDetail,
    VpnKeyListItem,
)
from infrastructure.persistence.database import get_session_context

router = APIRouter(prefix="/keys", tags=["VPN Keys"])


@router.get("", response_model=KeysListResponse)
async def list_keys(payload: dict = Depends(get_current_user)):
    """
    List all VPN keys for the authenticated user.

    Returns a list of all VPN keys with their status, usage, and metadata.
    Keys are grouped by active/inactive status.

    **Response includes:**
    - List of keys with basic info (name, type, usage, status)
    - Total count and active count
    - User's maximum allowed keys
    """
    telegram_id = int(payload["sub"])
    current_user_id = telegram_id  # User can only access their own keys

    logger.info(f"Listing VPN keys for user {telegram_id}")

    async with get_session_context() as session:
        # Get all keys for user
        result = await session.execute(
            text(
                """
                SELECT id, name, key_type, is_active, used_bytes, data_limit_bytes,
                       created_at, expires_at, last_seen_at, external_id
                FROM vpn_keys
                WHERE user_id = :telegram_id
                ORDER BY is_active DESC, created_at DESC
                """
            ),
            {"telegram_id": telegram_id},
        )

        rows = result.all()

        # Get user's max_keys limit
        user_result = await session.execute(
            text("SELECT max_keys FROM users WHERE telegram_id = :telegram_id"),
            {"telegram_id": telegram_id},
        )
        user_row = user_result.first()
        max_keys = user_row.max_keys if user_row else 2  # Default to 2

        # Convert to response objects
        keys: List[VpnKeyListItem] = []
        for row in rows:
            # Determine server name based on key_type
            server = "Outline Server" if row.key_type == "outline" else "WireGuard Server"

            keys.append(
                VpnKeyListItem(
                    id=str(row.id),
                    name=row.name or "Sin nombre",
                    key_type=row.key_type,
                    server=server,
                    is_active=row.is_active or False,
                    used_bytes=row.used_bytes or 0,
                    data_limit_bytes=row.data_limit_bytes or 0,
                    created_at=row.created_at,
                    expires_at=row.expires_at,
                    last_seen_at=row.last_seen_at,
                )
            )

        active_count = sum(1 for k in keys if k.is_active)

        logger.info(f"User {telegram_id} has {len(keys)} keys ({active_count} active)")

        return KeysListResponse(
            keys=keys,
            total_count=len(keys),
            active_count=active_count,
            max_keys=max_keys,
        )


@router.get("/{key_id}", response_model=VpnKeyDetail)
async def get_key_detail(key_id: str, payload: dict = Depends(get_current_user)):
    """
    Get detailed information for a specific VPN key.

    Includes connection string (key_data) for QR code generation and clipboard copy.

    **Path parameters:**
    - `key_id`: UUID of the VPN key

    **Security:** User can only access their own keys.
    """
    telegram_id = int(payload["sub"])
    current_user_id = telegram_id

    logger.info(f"Getting detail for VPN key {key_id} for user {telegram_id}")

    try:
        key_uuid = uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_key_id", "message": "ID de clave inválido"},
        )

    async with get_session_context() as session:
        result = await session.execute(
            text(
                """
                SELECT id, name, key_type, key_data, is_active, used_bytes,
                       data_limit_bytes, created_at, expires_at, last_seen_at,
                       billing_reset_at, external_id
                FROM vpn_keys
                WHERE id = :key_id AND user_id = :telegram_id
                """
            ),
            {"key_id": key_uuid, "telegram_id": telegram_id},
        )

        row = result.first()

        if not row:
            logger.warning(f"Key {key_id} not found for user {telegram_id}")
            raise HTTPException(
                status_code=404,
                detail={"error": "key_not_found", "message": "Clave no encontrada"},
            )

        # Determine server name
        server = "Outline Server" if row.key_type == "outline" else "WireGuard Server"

        logger.info(f"Key {key_id} retrieved successfully")

        return VpnKeyDetail(
            id=str(row.id),
            name=row.name or "Sin nombre",
            key_type=row.key_type,
            key_data=row.key_data or "",
            server=server,
            is_active=row.is_active or False,
            used_bytes=row.used_bytes or 0,
            data_limit_bytes=row.data_limit_bytes or 0,
            created_at=row.created_at,
            expires_at=row.expires_at,
            last_seen_at=row.last_seen_at,
            billing_reset_at=row.billing_reset_at,
            external_id=row.external_id,
        )


@router.get("/can-create", response_model=CanCreateKeyResponse)
async def can_create_key(payload: dict = Depends(get_current_user)):
    """
    Check if user can create new VPN keys.

    Returns detailed information about key creation capabilities:
    - General ability to create keys
    - Ability to create Outline keys specifically
    - Ability to create WireGuard keys specifically
    - Current key count and maximum allowed

    **Business rules:**
    - Users can have max 2 keys total (configurable)
    - Only 1 key per type (Outline/WireGuard)
    - Admins have unlimited keys
    """
    telegram_id = int(payload["sub"])
    current_user_id = telegram_id

    logger.info(f"Checking key creation capability for user {telegram_id}")

    async with get_session_context() as session:
        # Get user info
        user_result = await session.execute(
            text(
                """
                SELECT max_keys, role FROM users
                WHERE telegram_id = :telegram_id
                """
            ),
            {"telegram_id": telegram_id},
        )
        user_row = user_result.first()

        if not user_row:
            raise HTTPException(
                status_code=404,
                detail={"error": "user_not_found", "message": "Usuario no encontrado"},
            )

        max_keys = user_row.max_keys or 2
        role = user_row.role or "user"

        # Get current keys
        keys_result = await session.execute(
            text(
                """
                SELECT key_type, is_active FROM vpn_keys
                WHERE user_id = :telegram_id
                """
            ),
            {"telegram_id": telegram_id},
        )

        keys = keys_result.all()
        active_keys = [k for k in keys if k.is_active]
        current_count = len(active_keys)

        # Check per-type limits
        outline_keys = sum(1 for k in active_keys if k.key_type == "outline")
        wireguard_keys = sum(1 for k in active_keys if k.key_type == "wireguard")

        # Admins can create unlimited keys
        is_admin = role == "admin"
        can_create_general = is_admin or (current_count < max_keys)
        can_create_outline = is_admin or (outline_keys == 0)
        can_create_wireguard = is_admin or (wireguard_keys == 0)

        reason = None
        if not can_create_general:
            reason = f"Has alcanzado el límite de {max_keys} claves"
        elif not can_create_outline and not can_create_wireguard:
            reason = "Ya tienes una clave de cada tipo"

        logger.info(
            f"User {telegram_id}: can_create={can_create_general}, "
            f"outline={can_create_outline}, wireguard={can_create_wireguard}"
        )

        return CanCreateKeyResponse(
            can_create=can_create_general,
            can_create_outline=can_create_outline,
            can_create_wireguard=can_create_wireguard,
            current_count=current_count,
            max_keys=max_keys,
            reason=reason,
        )


@router.post("/create", response_model=CreateKeyResponse)
async def create_key(request: CreateKeyRequest, payload: dict = Depends(get_current_user)):
    """
    Create a new VPN key.

    **Request:**
    - `key_type`: "outline" or "wireguard"
    - `name`: Custom name for the key (max 30 chars)

    **Business rules:**
    - Validates user can create more keys
    - Validates user doesn't have a key of the same type
    - Admins can create unlimited keys
    - Regular users: max 2 keys total, 1 per type

    **Returns:**
    - Created key with connection string
    - QR data for display
    """
    telegram_id = int(payload["sub"])
    current_user_id = telegram_id

    logger.info(f"Creating {request.key_type} key for user {telegram_id}")

    # Validate key_type
    if request.key_type.lower() not in ["outline", "wireguard"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_key_type",
                "message": "Tipo de clave inválido. Debe ser 'outline' o 'wireguard'",
            },
        )

    # Import VpnService here to avoid circular imports
    from punq import Container

    from application.services.vpn_service import VpnService

    container = Container()
    vpn_service = container.resolve(VpnService)

    try:
        # Create the key using existing VpnService
        new_key = await vpn_service.create_key(
            telegram_id=telegram_id,
            key_type=request.key_type.lower(),
            key_name=request.name,
            current_user_id=current_user_id,
        )

        logger.info(f"Key created successfully: {new_key.id}")

        return CreateKeyResponse(
            id=new_key.id,
            name=new_key.name,
            key_type=new_key.key_type.value,
            key_data=new_key.key_data,
            qr_data=new_key.key_data,  # Same data for QR
            server=new_key.server,
            is_active=new_key.is_active,
            data_limit_bytes=new_key.data_limit_bytes,
            created_at=new_key.created_at,
        )

    except ValueError as e:
        logger.warning(f"Cannot create key: {e}")
        raise HTTPException(
            status_code=400,
            detail={"error": "cannot_create_key", "message": str(e)},
        )
    except Exception as e:
        logger.error(f"Error creating key: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "Error al crear la clave"},
        )


@router.patch("/{key_id}")
async def rename_key(
    key_id: str, request: RenameKeyRequest, payload: dict = Depends(get_current_user)
):
    """
    Rename a VPN key.

    **Path parameters:**
    - `key_id`: UUID of the VPN key

    **Request:**
    - `name`: New name (max 30 chars)

    **Security:** User can only rename their own keys.
    """
    telegram_id = int(payload["sub"])
    current_user_id = telegram_id

    logger.info(f"Renaming key {key_id} for user {telegram_id}")

    try:
        key_uuid = uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_key_id", "message": "ID de clave inválido"},
        )

    # Import VpnService
    from punq import Container

    from application.services.vpn_service import VpnService

    container = Container()
    vpn_service = container.resolve(VpnService)

    # Verify key exists and belongs to user
    async with get_session_context() as session:
        result = await session.execute(
            text("SELECT id FROM vpn_keys WHERE id = :key_id AND user_id = :telegram_id"),
            {"key_id": key_uuid, "telegram_id": telegram_id},
        )
        if not result.first():
            raise HTTPException(
                status_code=404,
                detail={"error": "key_not_found", "message": "Clave no encontrada"},
            )

    success = await vpn_service.rename_key(
        key_id=str(key_uuid),
        new_name=request.name,
        current_user_id=current_user_id,
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail={"error": "rename_failed", "message": "Error al renombrar la clave"},
        )

    logger.info(f"Key {key_id} renamed to {request.name}")

    return {"message": "Nombre actualizado", "name": request.name}


@router.delete("/{key_id}")
async def delete_key(key_id: str, payload: dict = Depends(get_current_user)):
    """
    Delete a VPN key.

    **Path parameters:**
    - `key_id`: UUID of the VPN key

    **Business rules:**
    - User must have referral_credits > 0 to delete keys
    - Admins can delete without credits
    - Action is irreversible

    **Security:** User can only delete their own keys.
    """
    telegram_id = int(payload["sub"])
    current_user_id = telegram_id

    logger.warning(f"User {telegram_id} attempting to delete key {key_id}")

    try:
        key_uuid = uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_key_id", "message": "ID de clave inválido"},
        )

    # Import VpnService
    from punq import Container

    from application.services.vpn_service import VpnService

    container = Container()
    vpn_service = container.resolve(VpnService)

    # Verify key exists and belongs to user
    async with get_session_context() as session:
        result = await session.execute(
            text("SELECT id FROM vpn_keys WHERE id = :key_id AND user_id = :telegram_id"),
            {"key_id": key_uuid, "telegram_id": telegram_id},
        )
        if not result.first():
            raise HTTPException(
                status_code=404,
                detail={"error": "key_not_found", "message": "Clave no encontrada"},
            )

    try:
        success = await vpn_service.delete_key(
            key_id=str(key_uuid),
            current_user_id=current_user_id,
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail={"error": "delete_failed", "message": "Error al eliminar la clave"},
            )

        logger.info(f"Key {key_id} deleted successfully")

        return {"message": "Clave eliminada"}

    except ValueError as e:
        logger.warning(f"Cannot delete key: {e}")
        raise HTTPException(
            status_code=400,
            detail={"error": "cannot_delete_key", "message": str(e)},
        )


@router.get("/{key_id}/usage", response_model=KeyUsageInfo)
async def get_key_usage(key_id: str, payload: dict = Depends(get_current_user)):
    """
    Get detailed usage information for a VPN key.

    **Path parameters:**
    - `key_id`: UUID of the VPN key

    **Returns:**
    - Used bytes and data limit
    - Remaining bytes
    - Usage percentage
    - Billing reset date
    """
    telegram_id = int(payload["sub"])
    current_user_id = telegram_id

    logger.info(f"Getting usage for key {key_id} for user {telegram_id}")

    try:
        key_uuid = uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_key_id", "message": "ID de clave inválido"},
        )

    async with get_session_context() as session:
        result = await session.execute(
            text(
                """
                SELECT used_bytes, data_limit_bytes, billing_reset_at
                FROM vpn_keys
                WHERE id = :key_id AND user_id = :telegram_id
                """
            ),
            {"key_id": key_uuid, "telegram_id": telegram_id},
        )

        row = result.first()

        if not row:
            logger.warning(f"Key {key_id} not found for user {telegram_id}")
            raise HTTPException(
                status_code=404,
                detail={"error": "key_not_found", "message": "Clave no encontrada"},
            )

        used_bytes = row.used_bytes or 0
        data_limit_bytes = row.data_limit_bytes or 0
        remaining_bytes = max(0, data_limit_bytes - used_bytes)
        usage_percentage = (used_bytes / data_limit_bytes * 100) if data_limit_bytes > 0 else 0.0

        return KeyUsageInfo(
            used_bytes=used_bytes,
            data_limit_bytes=data_limit_bytes,
            remaining_bytes=remaining_bytes,
            usage_percentage=round(usage_percentage, 2),
            billing_reset_at=row.billing_reset_at,
        )


@router.get("/{key_id}/connection", response_model=KeyUsageInfo)
async def get_key_connection(key_id: str, payload: dict = Depends(get_current_user)):
    """
    Get connection information for a VPN key.

    **Path parameters:**
    - `key_id`: UUID of the VPN key

    **Returns:**
    - Connection string (ss://... or WireGuard config)
    - QR code as base64 image (optional)
    - Connection instructions

    Note: This endpoint is similar to /{key_id} but focused on connection data.
    For simplicity, use the detail endpoint for connection info.
    """
    # For now, redirect to detail endpoint
    # This endpoint can be extended later to include QR code as base64
    raise HTTPException(
        status_code=404,
        detail={
            "error": "not_implemented",
            "message": "Usa el endpoint GET /keys/{key_id} para obtener la información de conexión",
        },
    )
